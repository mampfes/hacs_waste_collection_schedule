"""Abfallwirtschaft Nürnberger Land (nuernberger-land.de).

Demonstrates: the plain-vanilla ICS shape plus one extended ``IcsParser``
option — a single static GET keyed by an opaque location id, with
``split_at="/"`` because one VEVENT covers several bin types separated by
"/". HttpGetRetriever + the extended IcsParser + ICSTransformer do all the
work; this module only supplies the URL template and the waste-type map.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://abfuhrkalender.nuernberger-land.de/waste_calendar"
_FILTER = "rm:bio:p:dsd:poison"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Nürnberger Land"
    DESCRIPTION = "Source for Nürnberger Land"
    URL = "https://nuernberger-land.de"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Schwarzenbruck, Mühlbergstraße": {"id": 16952001},
        "Burgthann, Brunhildstr": {"id": 14398001},
        "Kirchensittenbach, Erlenweg": {"id": 15192001},
    }

    PARAMS = (text_field("id", "Location ID"),)

    retrieve = HttpGetRetriever(
        url=lambda id, **_: f"{_API_URL}/ical?id={id}&filter={_FILTER}"
    )
    parse = parsers.IcsParser(split_at="/")
    transform = ICSTransformer(
        type_value_map={
            "Restmüll": GENERAL_WASTE,
            "Biotonne": ORGANIC,
            "Gelber Sack": RECYCLABLES,
            "Papier": PAPER,
            "Giftmobil": HAZARDOUS,
        }
    )

    def __init__(self, id: int):
        super().__init__(id=id)
