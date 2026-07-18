from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsFieldMapPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LabelField,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

HOSTNAME = "eppingforestdc-self.achieveservice.com"
LOOKUP_COLLECTIONS = "6651dfb99a74d"


@final
class Source(BaseSource):
    TITLE = "Epping Forest District Council"
    DESCRIPTION = "Source for Epping Forest District Council, Essex, UK."
    URL = "https://www.eppingforestdc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "51 Crows Road Epping": {"uprn": "100090495060"},
        "47 Crows Road Epping": {"uprn": 100090495056},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting "
            "https://eppingforestdc-self.achieveservice.com/service/Check_your_collection_day "
            "and searching for your address. Your UPRN can also be found at "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        service_page="Check_your_collection_day",
        steps=[
            LookupStep(
                LOOKUP_COLLECTIONS,
                section="Address",
                form_values=lambda ctx, source: {
                    "LookupUPRN": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # Each service's human label lives in its OWN "...ServiceName" field
    # (e.g. "Food Waste Service"), not a name the source hard-codes.
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("FoodWasteServiceNextCollection", LabelField("FoodWasteServiceName")),
            ("FoodGardenServiceNextCollection", LabelField("FoodGardenServiceName")),
            ("GardenWasteServiceNextCollection", LabelField("GardenWasteServiceName")),
            ("RecyclingServiceNextCollection", LabelField("RecyclingServiceName")),
            (
                "GeneralWasteServiceNextCollection",
                LabelField("GeneralWasteServiceName"),
            ),
        ],
    )
    transform = RowTransformer(
        type_value_map={
            "food waste service": FOOD_WASTE,
            "food and garden service": ORGANIC,
            "garden waste service": GARDEN_WASTE,
            "recycling service": RECYCLABLES,
            "refuse service": GENERAL_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())
