from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.Tommekalender import TommekalenderParser
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Stavanger Kommune"
    DESCRIPTION = "Source for Stavanger Kommune, Norway"
    URL = "https://www.stavanger.kommune.no/"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestcaseI": {
            "id": "57bf9d36-722e-400b-ae93-d80f8e354724",
            "municipality": "Stavanger",
            "gnumber": "57",
            "bnumber": "922",
            "snumber": "0",
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
        url=(
            "https://www.stavanger.kommune.no/renovasjon-og-miljo/tommekalender/"
            "finn-kalender/show"
        ),
        params=lambda id, municipality, gnumber, bnumber, snumber, **_: {
            "ids": id,
            "id": id,
            "municipality": municipality,
            "gnumber": gnumber,
            "bnumber": bnumber,
            "snumber": snumber,
        },
        headers={"referer": "https://www.stavanger.kommune.no"},
    )
    parse = TommekalenderParser()
    transform = RowTransformer(
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Hage": wt.GARDEN_WASTE,
            "Mat": wt.FOOD_WASTE,
            "Papp og papir": wt.PAPER,
            "Papp/papir": wt.PAPER,
            "Plastemballasje": wt.RECYCLABLES,
            "Glass og metallemballasje": wt.GLASS,
        },
    )
