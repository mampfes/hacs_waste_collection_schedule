"""Landkreis Neumarkt, Germany (abfuhrplan-landkreis-neumarkt.de).

A two-level (city, then street) deployment of the shared abfuhrplan-*.de
platform, so the whole flow -- address path, 404 walk-up for suggestions and
the ``/getical`` form POST -- is the shared ``AbfuhrplanRetriever``.
"""

from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.service.AbfuhrplanDe import (
    AbfuhrplanRetriever,
    prepare_arg,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://www.abfuhrplan-landkreis-neumarkt.de"


@final
class Source(BaseSource):
    TITLE = "Landkreis Neumarkt"
    DESCRIPTION = "Source for Landkreis Neumarkt."
    URL = _BASE_URL
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "dietfurt industriestrasse": {"city": "dietfurt", "street": "industriestrasse"},
        "Parsberg, Bogenmühle": {"city": "parsberg", "street": "bogenmuehle"},
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
    )

    retrieve = AbfuhrplanRetriever(base_url=_BASE_URL, fields=("city", "street"))
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Papiertonne": PAPER,
            "Gelber Sack": RECYCLABLES,
            "Biotonne": ORGANIC,
        }
    )

    def __init__(self, city: str, street: str):
        super().__init__(city=prepare_arg(city), street=prepare_arg(street))
