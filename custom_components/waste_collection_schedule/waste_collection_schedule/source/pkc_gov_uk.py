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

_HOSTNAME = "my.pkc.gov.uk"
_PROCESS = "AF-Process-de9223b1-a7c6-408f-aaa3-aee33fd7f7fa"
_INITIAL_URL = (
    f"https://{_HOSTNAME}/AchieveForms/?mode=fill&consentMessage=yes"
    f"&form_uri=sandbox-publish://{_PROCESS}/"
    "AF-Stage-9fa33e2e-4c1b-4963-babf-4348ab8154bc/definition.json"
    f"&process=1&process_uri=sandbox-processes://{_PROCESS}&process_id={_PROCESS}"
)

_GENERAL = "Non-recyclable waste (green-lidded bin)"
_BLUE = "Paper and cardboard (blue-lidded bin)"
_GREY = "Plastic bottles, cans and cartons (grey-lidded bin)"
_BROWN = "Food and garden waste (brown-lidded bin)"
_PAPER = "Paper and cardboard"
_GARDEN = "Garden waste"
_COMMUNAL_FOOD = "Communal food waste"


@final
class Source(BaseSource):
    TITLE = "Perth and Kinross Council"
    DESCRIPTION = "Source for Perth and Kinross Council, UK."
    URL = "https://www.pkc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "7 St Marys Drive, Perth, PH2 7BY": {"uprn": "124022910"},
        "10A Crieff Road, Perth, PH1 5AF": {"uprn": 124003157},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            f"Find your UPRN by searching for your address at {_INITIAL_URL} or "
            "at https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        initial_url=_INITIAL_URL,
        steps=[
            LookupStep(
                "5c9267cee5efe",
                section="Bin collections",
                form_values=lambda ctx, source: {
                    "propertyUPRNQuery": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One summary row with a next and a following date per bin; a property the
    # lookup does not know comes back without them.
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("nextGeneralWasteCollectionDate", _GENERAL),
            ("nextGeneralWasteCollectionDate2nd", _GENERAL),
            ("nextBlueCollectionDate", _BLUE),
            ("nextBlueWasteCollectionDate2nd", _BLUE),
            ("nextGreyWasteCollectionDate", _GREY),
            ("nextGreyWasteCollectionDate2nd", _GREY),
            ("nextGardenandFoodWasteCollectionDate", _BROWN),
            ("nextGardenandFoodWasteCollectionDate2nd", _BROWN),
            ("nextPaperWasteCollectionDate", _PAPER),
            ("nextPaperWasteCollectionDate2nd", _PAPER),
            ("nextGardenWasteCollectionDate", _GARDEN),
            ("nextGardenWasteCollectionDate2nd", _GARDEN),
            ("nextCommunalFoodWasteCollectionDate", _COMMUNAL_FOOD),
        ],
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
    transform = RowTransformer(
        type_value_map={
            _GENERAL: wt.GENERAL_WASTE,
            _BLUE: wt.PAPER,
            _GREY: wt.RECYCLABLES,
            _BROWN: wt.ORGANIC,
            _PAPER: wt.PAPER,
            _GARDEN: wt.GARDEN_WASTE,
            _COMMUNAL_FOOD: wt.FOOD_WASTE,
        },
        carry_raw_label=True,
    )
