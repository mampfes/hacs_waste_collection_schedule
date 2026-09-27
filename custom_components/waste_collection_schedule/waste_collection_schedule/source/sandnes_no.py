from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.Tommekalender import TommekalenderParser
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Sandnes Kommune"
    DESCRIPTION = "Source for Sandnes Kommune, Norway"
    URL = "https://www.sandnes.kommune.no/"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestcaseI": {
            "id": "181e5aac-3c88-4b0b-ad46-3bd246c2be2c",
            "municipality": "Sandnes kommune 2020",
            "gnumber": "62",
            "bnumber": "281",
            "snumber": "0",
        },
        "TestcaseII": {
            "id": "cb263140-1743-4459-ab3a-a9677884904f",
            "municipality": "Sandnes kommune 2020",
            "gnumber": 33,
            "bnumber": 844,
            "snumber": 0,
        },
    }

    PARAMS = (
        text_field("id", "Property id"),
        municipality(),
        text_field("gnumber", "Gårdsnummer"),
        text_field("bnumber", "Bruksnummer"),
        text_field("snumber", "Seksjonsnummer"),
    )

    retrieve = HttpGetRetriever(
        url="https://www.hentavfall.no/rogaland/sandnes/tommekalender/show",
        params=lambda id, municipality, gnumber, bnumber, snumber, **_: {
            "id": id,
            "municipality": municipality,
            "gnumber": gnumber,
            "bnumber": bnumber,
            "snumber": snumber,
        },
    )
    parse = TommekalenderParser()
    transform = RowTransformer(
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Plastemballasje": wt.RECYCLABLES,
            "Matavfall": wt.FOOD_WASTE,
            "Hageavfall": wt.GARDEN_WASTE,
            "Papp og papir": wt.PAPER,
            "Glass og metallemballasje": wt.GLASS,
        },
    )
