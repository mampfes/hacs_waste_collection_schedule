from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.NorkartMinRenovasjon import (
    MinRenovasjonParser,
    MinRenovasjonRetriever,
)
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Min Renovasjon"
    DESCRIPTION = "Source for Norkart Komtek MinRenovasjon (Norway)."
    URL = "https://www.norkart.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    REGIONS = (
        region(
            "ROAF (Romerike Avfallsforedling IKS)",
            url="https://www.roaf.no",
            street_name="Solvangen",
            house_number="2",
            street_code="12950",
            county_id="3205",
        ),
    )

    TEST_CASES: ClassVar[dict] = {
        "Sandvika Rådhus": {
            "street_name": "Rådhustorget",
            "house_number": 2,
            "street_code": 2469,
            "county_id": 3024,
        },
        "Lillehammer Åsmarkvegen 111": {
            "street_name": "Åsmarkvegen",
            "house_number": 111,
            "street_code": 6530,
            "county_id": 3405,
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look up your address with the Kartverket address API, for example "
            "https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012. "
            "`street_code` is the result's `adressekode` and `county_id` its "
            "`kommunenummer`."
        ),
    }

    PARAMS = (
        street("street_name"),
        house_number(),
        text_field("street_code", "Street code"),
        text_field("county_id", "Municipality number"),
    )

    retrieve = MinRenovasjonRetriever()
    parse = MinRenovasjonParser()
    transform = RowTransformer(
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Mat-/restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Våtorganisk": wt.FOOD_WASTE,
            "Hageavfall": wt.GARDEN_WASTE,
            "Papir": wt.PAPER,
            "Papp": wt.PAPER,
            "Papp og papir": wt.PAPER,
            "Papir, papp": wt.PAPER,
            "Papp, papir, kartong": wt.PAPER,
            "Plast": wt.RECYCLABLES,
            "Plastemballasje": wt.RECYCLABLES,
            "Metaller": wt.RECYCLABLES,
            "Drikkekartonger": wt.RECYCLABLES,
            "Glass-/metallemb": wt.RECYCLABLES,
            "Glass- og metallemballasje": wt.RECYCLABLES,
            "Hermetikk- og glassemballasje": wt.RECYCLABLES,
            "Farlig avfall": wt.HAZARDOUS,
            "Spesialavfall": wt.HAZARDOUS,
            "Tekstiler": wt.TEXTILES,
            "Tekstiler, klær og sko": wt.TEXTILES,
            "Grovavfall": wt.BULKY_WASTE,
        },
    )
