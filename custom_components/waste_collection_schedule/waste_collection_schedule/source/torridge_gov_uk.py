import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsLabelSplitPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "torridgedc-self.achieveservice.com"
_DAY_MONTH = date_parsers.next_weekday("%a %d %b")
_RELATIVE = {"today": 0, "tomorrow": 1}


def _next_date(*args: str) -> datetime.date:
    """The first date of "Wed 30 Sep then every Wed" (or "Today", "Tomorrow")."""
    text = re.sub(r"\(.*?\)", "", args[-1].split(" then ")[0]).strip()
    if text.lower() in _RELATIVE:
        return datetime.date.today() + datetime.timedelta(days=_RELATIVE[text.lower()])
    return _DAY_MONTH(text)


@final
class Source(BaseSource):
    TITLE = "Torridge Council"
    DESCRIPTION = "Source for torridge.gov.uk services for Torridge, UK."
    URL = "https://torridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GARDEN_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10093911050"},
        "Test_002": {"uprn": 10002296087},
        "Test_003": {"uprn": "200001644184"},
        "Test_004": {"uprn": 100040385608},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="My_property_information",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[
            LookupStep(
                "6583107397653",
                section="Search",
                form_values=lambda ctx, source: {
                    "uprn": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row, a text per round: "Refuse: Fri 2 Oct then every alternate Fri",
    # or "GardenBin: No GardenBin waste collection for this address".
    preprocess = AchieveFormsLabelSplitPreprocessor(
        field=("Round1", "Round2", "Round3"), separator=": ", split_at="first"
    )
    transform = RowTransformer(
        parse_date=_next_date,
        skip_unparseable_dates=True,
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "GardenBin": wt.GARDEN_WASTE,
        },
    )
