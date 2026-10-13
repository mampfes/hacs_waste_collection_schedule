from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.retrievers import FanOutRetriever
from waste_collection_schedule.service.ComD import (
    ComdCategoryLookup,
    ComdCategoryParser,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Gmina Środa Śląska"
    DESCRIPTION = "Source for Gmina Środa Śląska, Poland"
    URL = "https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.com-d.pl/komunalne/harm/sroda-slaska, select your "
            "locality or Środa Śląska district, and enter the final part of its URL "
            "as `location`. `property_type` is `all` (default), `single_family` or "
            "`multi_family`; select the dwelling type when the provider publishes "
            "separate schedules."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Szczepanów": {"location": "szczepanow"},
        "Środa Śląska I rejon": {"location": "sroda-slaska-i-rejon"},
        "Ciechów": {"location": "ciechow"},
        "Ciechów single-family": {
            "location": "ciechow",
            "property_type": "single_family",
        },
        "Ciechów multifamily": {"location": "ciechow", "property_type": "multi_family"},
    }

    PARAMS: ClassVar[list] = [
        text_field("location", "Location"),
        dropdown(
            "property_type",
            ["all", "single_family", "multi_family"],
            "Property type",
            default="all",
        ),
    ]

    retrieve = FanOutRetriever(
        prepare=ComdCategoryLookup("sroda-slaska"),
        targets=lambda source, urls: urls,
    )
    parse = parsers.EachResponse(
        ComdCategoryParser(
            {
                "single_family": "zabudowa jednorodzinna",
                "multi_family": "zabudowa wielorodzinna",
            }
        )
    )
    transform = ICSTransformer(
        type_value_map={
            "szkło": wt.GLASS,
            "inne": wt.TEXTILES,
            "zbiórki": wt.BULKY_WASTE,
            "papier": wt.PAPER,
            "odpady zmieszane": wt.GENERAL_WASTE,
            "odpady biodegradowalne": wt.ORGANIC,
            "metale i tworzywa sztuczne": wt.RECYCLABLES,
        },
    )
