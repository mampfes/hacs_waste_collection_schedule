"""Three Rivers District Council - Collection calendar.

Three Rivers runs its own AchieveForms portal (``my.threerivers.gov.uk``), no
login needed. Picking an address takes one lookup (postcode -> addresses keyed
by UPRN); the calendar takes two: a token lookup for the UPRN, then the
calendar lookup that returns one ``{JobName, Date}`` row per collection. The
same postcode lookup fills the config flow's address dropdown.
"""

from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.retrievers import detached_source
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowFieldsPreprocessor,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer, label_cleaner

HOSTNAME = "my.threerivers.gov.uk"
INITIAL_URL = f"https://{HOSTNAME}/fillform/?iframe_id=fillform-frame-1&db_id="
SECTION = "Your address details"

LOOKUP_ADDRESSES = "569502c503341"  # postcode -> addresses (keyed by UPRN)
LOOKUP_TOKEN = "58986058d4be0"  # UPRN -> one-off token for the calendar lookup
LOOKUP_CALENDAR = "58ac332f9e831"  # UPRN + token -> {JobName, Date} rows


def _extract_token(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    if not rows:
        raise SourceArgumentException("uprn", "No calendar token for this UPRN")
    context["token"] = next(iter(rows.values()))["token"]


def _calendar_form_values(context: dict, source: Any) -> dict:
    # The calendar lookup answers 500 without the two date fields the form
    # fills in itself: today, and two weeks on.
    today = date.today()
    return {
        "UPRN": {"value": source.params["uprn"]},
        "userType": {"value": "Self"},
        "token": {"value": context["token"]},
        "todaysdate": {"value": f"{today.isoformat()}T00:00:00"},
        "twoweeks": {"value": f"{(today + timedelta(days=14)).isoformat()}T00:00:00"},
    }


@final
class Source(BaseSource):
    TITLE = "Three Rivers District Council"
    DESCRIPTION = "Source for Three Rivers District Council, Hertfordshire."
    URL = "https://www.threerivers.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Eastbury Avenue": {"postcode": "HA6 3LJ", "uprn": "200000940124"},
    }

    PARAMS = (
        cascading_select(
            ("postcode", field_terms.POSTCODE),
            ("uprn", field_terms.ADDRESS),
        ),
    )

    # One AchieveForms conversation serves both the fetch and the config flow's
    # address list; only the steps differ.
    _ADDRESSES = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ADDRESSES,
                section=SECTION,
                form_values=lambda ctx, source: {
                    "postcode_search": {"value": source.params["postcode"]}
                },
            ),
        ],
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[tuple[str, str]]:
        """Address options for the postcode chosen; the postcode is free text."""
        postcode = selections.get("postcode")
        if field != "uprn" or not postcode:
            return []
        response = cls._ADDRESSES(detached_source({"postcode": postcode}))
        rows = response.get("integration", {}).get("transformed", {}).get("rows_data")
        return [(row["display"], row["uprn"]) for row in (rows or {}).values()]

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_TOKEN,
                section=SECTION,
                no_retry="true",
                form_values=lambda ctx, source: {
                    "UPRN": {"value": source.params["uprn"]},
                    "userType": {"value": "Self"},
                },
                extract=_extract_token,
            ),
            LookupStep(
                LOOKUP_CALENDAR,
                section=SECTION,
                form_values=_calendar_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsRowFieldsPreprocessor(
        date_field="Date",
        label_fields=("JobName",),
        dedupe=True,  # one row per round, so a date repeats its bin type
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d-%m-%Y"),
        clean=label_cleaner(
            remap={
                "140 REFUSE": "Refuse",
                "140 RECYCLING": "Recycling",
                "140 FOOD": "Food",
            }
        ),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
        },
    )
