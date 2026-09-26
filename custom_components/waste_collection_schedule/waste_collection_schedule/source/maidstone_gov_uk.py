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

_HOSTNAME = "my.maidstone.gov.uk"


@final
class Source(BaseSource):
    TITLE = "Maidstone Borough Council"
    DESCRIPTION = "Source for maidstone.gov.uk services for Maidstone Borough Council."
    URL = "https://maidstone.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "10022892379"},
        "Test_002": {"uprn": 10014307164},
        "Test_003": {"uprn": "200003674881"},
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
        initial_url=f"https://{_HOSTNAME}/service/Find-your-bin-day",
        skip_landing_page=True,
        auth_test_url=f"https://{_HOSTNAME}/apibroker/domain/{_HOSTNAME}",
        steps=[
            LookupStep(
                "654b7b6478deb",
                section="Lookup",
                form_values=lambda ctx, source: {
                    "AddressData": {"value": source.params["uprn"]},
                    "AddressUPRN": {"value": source.params["uprn"]},
                },
                no_retry="true",
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row, keyed by the UPRN, with a "<Service>_NextCollectionDateMM" and a
    # "<Service>_Active" flag per service ("DomesticResidual", "GardenWaste").
    preprocess = AchieveFormsDynamicRowsPreprocessor(
        r"^([A-Za-z]+)_NextCollectionDateMM$",
        row_key=lambda source: source.params["uprn"] if source else "0",
        split_label=True,
        key_filter=lambda key, row: row.get(f"{key.split('_')[0]}_Active") != "N",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Domestic Residual": wt.GENERAL_WASTE,
            "Communal Residual": wt.GENERAL_WASTE,
            "Domestic Recycling": wt.RECYCLABLES,
            "Communal Recycling": wt.RECYCLABLES,
            "Domestic Food": wt.FOOD_WASTE,
            "Communal Food": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            "Clinical Waste": wt.HAZARDOUS,
            "Bulky Waste": wt.BULKY_WASTE,
            # a repair visit for a damaged bin, not a collection
            "Bin Maintenance": None,
        },
        carry_raw_label=True,
    )
