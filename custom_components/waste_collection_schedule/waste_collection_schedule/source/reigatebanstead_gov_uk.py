import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "my.reigate-banstead.gov.uk"
_TOKEN_LOOKUP_ID = "595ce0f243541"
_SCHEDULE_LOOKUP_ID = "609d41ca89251"


def _extract_token(response: dict, context: dict) -> None:
    rows = response["integration"]["transformed"]["rows_data"]
    context["token"] = rows["0"]["Token"]


def _schedule_form_values(context: dict, source: Any) -> dict:
    today = datetime.date.today()
    return {
        "uprnPWB": {"value": str(source.params["uprn"])},
        "minDate": {"value": today.isoformat()},
        # The calendar serves at most four weeks ahead.
        "maxDate": {"value": (today + datetime.timedelta(days=28)).isoformat()},
        "tokenString": {"value": context["token"]},
    }


@final
class Source(BaseSource):
    TITLE = "Reigate & Banstead Borough Council"
    DESCRIPTION = "Source for reigate-banstead.gov.uk services for the Reigate & Banstead Borough, UK."
    URL = "https://reigate-banstead.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 68110755},
        "Test_002": {"uprn": "000068110755"},
        "Test_003": {"uprn": "68101147"},  # commercial refuse collection
        "Test_004": {"uprn": "000068101147"},  # commercial refuse collection
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/",
    }

    # A GET lookup issues a one-time token the schedule lookup must carry.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}/service/Bins_and_recycling___collections_calendar",
        skip_landing_page=True,
        steps=[
            LookupStep(
                _TOKEN_LOOKUP_ID,
                method="GET",
                no_retry="true",
                extract=_extract_token,
            ),
            LookupStep(
                _SCHEDULE_LOOKUP_ID,
                form_values=_schedule_form_values,
                no_retry="true",
            ),
        ],
    )
    # The rows hold one rendered HTML fragment: a date heading per collection
    # day, followed by a list of the bins emptied that day.
    parse = parsers.HtmlLabelledDates(
        "div:has(> div > h3)",
        label="ul span",
        date="h3",
        all_labels=True,
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        from_json_key=("integration", "transformed", "rows_data", "0", "root"),
    )
    transform = RowTransformer(
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "Mixed recycling": wt.RECYCLABLES,
            "Trade - mixed recycling": wt.RECYCLABLES,
            "Glass": wt.GLASS,
            "Mixed cans": wt.RECYCLABLES,
            "Plastic": wt.RECYCLABLES,
            "Paper and cardboard": wt.PAPER,
            "Trade - paper and cardboard": wt.PAPER,
            "Refuse": wt.GENERAL_WASTE,
            "Trade - refuse": wt.GENERAL_WASTE,
            "Garden waste": wt.GARDEN_WASTE,
        },
    )
