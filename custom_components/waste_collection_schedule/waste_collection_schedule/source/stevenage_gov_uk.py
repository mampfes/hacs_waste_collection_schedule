from collections.abc import Iterable
from datetime import date
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "stevenage-self.achieveservice.com"
BASE_URL = f"https://{HOSTNAME}"
TOKEN_LOOKUP_ID = "5e55337a540d4"
COLLECTION_LOOKUP_ID = "64ba8cee353e6"


def _extract_token(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    context["token"] = rows.get("0", {}).get("token", "")


def _collection_form_values(context: dict, source: Any) -> dict:
    today = date.today()
    # A year-ahead date built by incrementing the year on the same month/day,
    # matching the original string arithmetic (not calendar-accurate on a
    # leap day, but that is the provider's existing behaviour, not ours to fix).
    max_date = f"{today.year + 1}-{today.month:02d}-{today.day:02d}"
    return {
        "token": {"value": context["token"]},
        "LLPGUPRN": {"value": source.params["uprn"]},
        "MinimumDateLookAhead": {"value": today.isoformat()},
        "MaximumDateLookAhead": {"value": max_date},
    }


@final
class Source(BaseSource):
    TITLE = "Stevenage Borough Council"
    DESCRIPTION = "Source for Stevenage."
    URL = "https://www.stevenage.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [FOOD_WASTE, GENERAL_WASTE, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Chepstow Close": {"uprn": "100080879233"},
        "Rectory Lane": {"uprn": "100081137566"},
        "Neptune Gate": {"uprn": "200000585910"},
    }

    PARAMS = (uprn(),)

    # Stevenage fetches a one-time token via a GET-mode runLookup call before
    # the real POST lookup, which needs that token as a form field.
    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        service_page="Check_your_household_bin_collection_days",
        steps=[
            LookupStep(
                TOKEN_LOOKUP_ID,
                method="GET",
                extract=_extract_token,
            ),
            LookupStep(
                COLLECTION_LOOKUP_ID,
                form_values=_collection_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = JsonTransformer(
        date_key="collectiondate",
        type_key="bintype",
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "general waste": GENERAL_WASTE,
            "recycling": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[dict]":
        # rows_data is a dict keyed by row index ({"0": {...}, "1": {...}}),
        # one row per collection; JsonTransformer needs each row, not the
        # whole rows_data dict as a single record.
        yield from (rows.values() if isinstance(rows, dict) else rows)
