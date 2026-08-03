from collections.abc import Iterable
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    AchieveFormsRowsPreprocessor,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

HOSTNAME = "contact.lincoln.gov.uk"
INITIAL_URL = (
    "https://contact.lincoln.gov.uk/AchieveForms/?mode=fill&consentMessage=yes"
    "&form_uri=sandbox-publish://AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196/"
    "AF-Stage-a1c0af0f-fec1-4419-80c0-0dd4e1d965c9/definition.json&process=1"
    "&process_uri=sandbox-processes://AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196"
    "&process_id=AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196"
)
LOOKUP_ID = "62aafd258f72c"

# (date field, label, frequency field). A "fortnightly"/"weekly" frequency
# projects the next date forward for a year; anything else (e.g. an
# unsubscribed or as-required service) is reported once, matching the
# original single lookup that only ever returned the *next* date per bin.
BIN_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("refusenextdate", "Refuse", "refuse_freq"),
    ("recyclenextdate", "Recycling", "recycle_freq"),
    ("gardennextdate", "Garden", "garden_freq"),
)


def _property_row_key(source: "BaseSource | None") -> str:
    """The row this property's schedule is under: the lookup keys by UPRN."""
    return str(source.params["uprn"]) if source is not None else ""


def _describe(row: dict, source: "BaseSource | None" = None) -> "Iterable[Schedule]":
    """Turn the property's row into one recurring schedule per bin."""
    for date_field, label, freq_field in BIN_FIELDS:
        raw_date = row.get(date_field)
        if not raw_date:
            continue
        start = datetime.strptime(raw_date, "%Y-%m-%d").date()
        frequency = str(row.get(freq_field) or "").strip().lower()
        if frequency == "fortnightly":
            step, count = recurrence.FORTNIGHTLY, 27
        elif frequency == "weekly":
            step, count = recurrence.WEEKLY, 53
        else:
            step, count = recurrence.WEEKLY, 1
        yield Schedule(label, start, step, count)


@final
class Source(BaseSource):
    TITLE = "City Of Lincoln Council"
    DESCRIPTION = "Source for City Of Lincoln Council."
    URL = "https://www.lincoln.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "LN5 7SH 000235024846": {"postcode": "LN5 7SH", "uprn": "000235024846"},
        "LN2 4SA, 000235042214": {"postcode": "LN24Sa", "uprn": 235042214},
        "LN2 4EB 000235036597": {"postcode": " Ln 24 eB ", "uprn": 235036597},
    }

    PARAMS = (postcode(), uprn())

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        auth_test_url=f"https://{HOSTNAME}/apibroker/domain/{HOSTNAME}",
        # The landing page itself 403s a non-browser GET; authapi accepts the
        # same URL as a literal `uri` value without fetching it first.
        skip_landing_page=True,
        steps=[
            LookupStep(
                LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "chooseaddress": {"value": source.params["uprn"]},
                    "postcode": {"value": source.params["postcode"]},
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # The lookup returns every property at the postcode, keyed by UPRN; only
    # the chosen one is this schedule, and its row carries a next date plus a
    # cadence per bin rather than explicit collection dates.
    preprocess = Compose(
        AchieveFormsRowsPreprocessor(row_key=_property_row_key),
        RecurrenceExpander(_describe),
    )
    transform = RowTransformer(
        type_value_map={
            "refuse": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
        },
    )

    def __init__(self, postcode: str, uprn: str | int):
        normalised_postcode = postcode.replace(" ", "").upper()
        normalised_postcode = normalised_postcode[:3] + " " + normalised_postcode[3:]
        super().__init__(postcode=normalised_postcode, uprn=str(uprn).zfill(12))
