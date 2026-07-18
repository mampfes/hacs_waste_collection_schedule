"""Abfallabholung Wermelskirchen (bavweb.de).

Demonstrates: a static, param-built ICS GET whose "street" query argument is
a base64 token of a fixed prefix plus the street name, and whose response
mis-declares its charset (umlauts corrupt unless ``response.encoding`` is
forced to UTF-8 before ``.text`` is read) -- both handled in a small
source-defined ``parse`` around the plain ``ICS()`` service class; retrieval
itself is the standard ``HttpGetRetriever``. ``house_number`` is accepted for
parity with the provider's other calendars but, like the legacy source, is
not actually part of the request: this endpoint serves one calendar per
street, not per address.
"""

import base64
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_URL = "https://abfallkalender.regioit.de/kalender-bav/downloadfile.jsp"


def _normalize_street(value: str) -> str:
    """Fix a street name that was double-encoded (UTF-8 bytes read as Latin-1)."""
    if "Ã" in value:
        try:
            return value.encode("latin1").decode("utf-8")
        except UnicodeError:
            return value
    return value


def _street_token(street: str) -> str:
    normalized = _normalize_street(street)
    return base64.b64encode(f"Wermelskirchen42929{normalized}".encode("latin1")).decode(
        "ascii"
    )


def _params(street: str, **_) -> dict:
    return {
        "format": "ics",
        "jahr": str(datetime.now().year),
        "ort": "Wermelskirchen",
        "strStatic": _street_token(street),
        "zeit": "1:00:00",
        "fraktion": [8, 12, 13, 15, 16, 22, 23, 24],
    }


@final
class Source(BaseSource):
    TITLE = "Wermelskirchen"
    DESCRIPTION = "Source for Abfallabholung Wermelskirchen, Germany"
    URL = "https://www.bavweb.de/Bergischer-Abfallwirtschaftsverband/Abfuhrkalender-Service/Wermelskirchen/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Rathaus": {"street": "Telegrafenstraße", "house_number": "29"},
        "Krankenhaus": {"street": "Königstraße", "house_number": "100"},
        "Mehrzweckhalle": {"street": "An der Mehrzweckhalle", "house_number": "1"},
    }

    PARAMS = (
        street(field="street"),
        house_number(field="house_number", optional=True),
    )

    retrieve = HttpGetRetriever(url=_URL, params=_params)

    def parse(self, response, source=None):
        response.encoding = "utf-8"
        return ICS().convert(response.text)

    transform = ICSTransformer(
        type_value_map={
            "restmülltonne 2-wöchentlich": GENERAL_WASTE,
            "restmülltonne 4-wöchentlich": GENERAL_WASTE,
            "restmülltonne 6-wöchentlich": GENERAL_WASTE,
            "gelber sack / tonne": RECYCLABLES,
            "papiertonne": PAPER,
            "biotonne": ORGANIC,
            "schadstoffmobil": HAZARDOUS,
            "weihnachtsbaum": GARDEN_WASTE,
        }
    )

    def __init__(self, street: str, house_number: "str | int | None" = None):
        super().__init__(street=street, house_number=house_number)
