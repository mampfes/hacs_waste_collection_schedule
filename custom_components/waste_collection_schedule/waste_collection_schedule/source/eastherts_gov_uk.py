import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsDynamicRowsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "eastherts-self.achieveservice.com"
_WEEKDAY_DAY_MONTH = date_parsers.next_weekday("%A %d %B")


def _next_date(text: str) -> datetime.date:
    """ "Tuesday 6th October" -> its next occurrence (no year is given)."""
    return _WEEKDAY_DAY_MONTH(re.sub(r"(\d+)(?:st|nd|rd|th)\b", r"\1", text))


@final
class Source(BaseSource):
    TITLE = "East Herts Council"
    DESCRIPTION = "Source for www.eastherts.gov.uk services for East Herts Council."
    URL = "https://www.eastherts.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "UPRN only": {"uprn": "100080738904"},
        "UPRN 10033104539": {"uprn": "10033104539"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="Bins___When_are_my_Bin_Collection_days",
        steps=[
            LookupStep(
                "683d9ff0e299d",
                section="Collection Days",
                form_values=lambda ctx, source: {
                    "inputUPRN": {"value": source.params["uprn"]}
                },
                no_retry="true",
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row with a "<Bin>NextDate" per bin: "Tuesday 6th October".
    preprocess = AchieveFormsDynamicRowsPreprocessor(
        r"^(.+)NextDate$", parse_date=_next_date
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Paper": wt.PAPER,
            "Food": wt.FOOD_WASTE,
            "GW": wt.GARDEN_WASTE,
        },
    )
