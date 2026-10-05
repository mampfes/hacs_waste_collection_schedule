from typing import ClassVar, final

from waste_collection_schedule import date_parsers, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    city,
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.service.SismsPl import (
    OWNER_IDS,
    TYPE_VALUE_MAP,
    SismsParser,
    SismsRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "SISMS.pl / BLISKO"
    DESCRIPTION = "Source for SISMS.pl / BLISKO."
    URL = "https://sisms.pl"
    COUNTRY = "pl"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "188 Bobrza ul. St. Staszica 3": {
            "owner_id": 188,
            "town": "Bobrza",
            "street": "ul. St. Staszica",
            "street_address": 23,
        },
        "Jeżewo Ciemniki 2a": {
            "owner": "Jeżewo",
            "town": "Ciemniki",
            "town_address": "2a",
        },
    }

    PARAMS = (
        alternatives(
            [municipality("owner")],
            [text_field("owner_id", "Owner ID")],
        ),
        city("town"),
        alternatives(
            [text_field("town_address", "House number (in the town)")],
            [street("street"), house_number("street_address")],
        ),
    )

    REGIONS = tuple(
        regions.region(name.strip(), owner=name.strip()) for name in OWNER_IDS.values()
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Owner: your gmina as listed (or its numeric owner id, which the "
            "search page at https://sisms.pl requests as ownerId). Town: your "
            "town (Miejscowość). Then either the house number in the town, or "
            "the street (Ulica) and house number (Numer domu)."
        ),
    }

    retrieve = SismsRetriever()
    parse = SismsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map=TYPE_VALUE_MAP,
    )
