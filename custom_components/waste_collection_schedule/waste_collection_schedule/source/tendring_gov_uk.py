from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsFieldMapPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "tendring-self.achieveservice.com"
LOOKUP_COLLECTIONS = "6347acbadc425"


@final
class Source(BaseSource):
    TITLE = "Tendring District Council"
    DESCRIPTION = "Source for Tendring District Council, Essex, UK."
    URL = "https://www.tendringdc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1 Queens Road, Clacton-on-Sea": {"uprn": "100090613962"},
        "18 High Street, Manningtree": {"uprn": 100091459763},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting "
            "https://tendring-self.achieveservice.com/en/service/"
            "Rubbish_and_recycling_collection_days and searching for your "
            "address. Your UPRN can also be found at "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        service_page="Rubbish_and_recycling_collection_days",
        steps=[
            LookupStep(
                LOOKUP_COLLECTIONS,
                section="Address",
                form_values=lambda ctx, source: {
                    "selectedUPRN": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("nextResidualCollection", "Residual waste"),
            ("nextGreenCollection", "Green recycling box"),
            ("nextRedCollection", "Red recycling box"),
            ("nextFoodCollection", "Food waste", "eligibleFoodCollection"),
            ("nextGardenCollection", "Garden waste", "activeGardenCollection"),
        ],
        # API returns "DD/MM/YYYY HH:MM:SS"; truncate before the day-first parse.
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        truncate=10,
    )
    transform = RowTransformer(
        type_value_map={
            "residual waste": GENERAL_WASTE,
            "green recycling box": RECYCLABLES,
            "red recycling box": RECYCLABLES,
            "food waste": FOOD_WASTE,
            "garden waste": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())
