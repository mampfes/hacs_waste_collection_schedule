import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsFieldMapPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "my.dudley.gov.uk"


def _form(context, source):
    today = datetime.date.today()
    return {
        "uprnToCheck": {"value": source.params["uprn"].zfill(12)},
        "NextCollectionFromDate": {"value": today.strftime("%Y-%m-%d")},
        "NextCollectionToDate": {
            "value": (today + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        },
    }


@final
class Source(BaseSource):
    TITLE = "Dudley Metropolitan Borough Council"
    DESCRIPTION = "Source for Dudley Metropolitan Borough Council, UK."
    URL = "https://dudley.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.FOOD_WASTE, wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "90090715"},
        "Test_002": {"uprn": 90104555},
        "Test_003": {"uprn": "90164803"},
        "Test_004": {"uprn": 90092621},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for "
            "your address."
        ),
    }

    # The next collection of each bin within the coming 60 days.
    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=f"https://{_HOSTNAME}",
        skip_landing_page=True,
        steps=[LookupStep("69a04ac70086b", form_values=_form, no_retry="true")],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("recyclingDate", "Recycling"),
            ("foodDate", "Food"),
            ("refuseDate", "Refuse"),
        ],
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Refuse": wt.GENERAL_WASTE,
        },
    )
