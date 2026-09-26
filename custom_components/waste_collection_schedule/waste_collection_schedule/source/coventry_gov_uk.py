from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsFieldMapPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsXmlRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "myaccount.coventry.gov.uk"

_REFUSE = "Household waste (green-lidded bin)"
_RECYCLING = "Recycling (blue-lidded bin)"
_GARDEN = "Garden waste (brown-lidded bin)"
_FOOD = "Food waste caddy"


@final
class Source(BaseSource):
    TITLE = "Coventry City Council"
    DESCRIPTION = "Source for waste collection services for Coventry City Council"
    URL = "https://www.coventry.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100070666040"},
        "Test_002": {"uprn": 100070666041},
        "Test_003": {"uprn": "100070649599"},
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
        initial_url=f"https://{_HOSTNAME}/service/find_my_bin_day",
        steps=[
            LookupStep(
                "6a675c200be8f",
                form_values=lambda ctx, source: {
                    "Address_UPRN": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    # The Bartec integration answers in XML: one row, a date per bin, and
    # 0001-01-01 for a bin the property does not have.
    parse = AchieveFormsXmlRowsParser()
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("Bartec_Refuse_Date", _REFUSE),
            ("Bartec_Recycling_Date", _RECYCLING),
            ("Bartec_Garden_Date", _GARDEN),
            ("Bartec_Food_Date", _FOOD),
        ],
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        truncate=10,
    )
    transform = RowTransformer(
        type_value_map={
            _REFUSE: wt.GENERAL_WASTE,
            _RECYCLING: wt.RECYCLABLES,
            _GARDEN: wt.GARDEN_WASTE,
            _FOOD: wt.FOOD_WASTE,
        },
        carry_raw_label=True,
    )
