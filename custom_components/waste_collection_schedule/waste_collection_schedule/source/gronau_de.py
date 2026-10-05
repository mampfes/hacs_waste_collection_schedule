"""Abfallkalender Gronau (regio iT "kalender-wml", Germany).

Demonstrates ``IcsSessionRetriever`` for a per-year download keyed by an id the
site only publishes inside its own page: the calendar page carries the street
list as a JavaScript object (``streetList = {"Alter Markt": 123, ...}``), so a
single preparatory request resolves the configured street to its id, and the
download then takes that id plus the year and every waste stream the calendar
offers. From October on the following year is fetched too, so the lookahead
window the ICS conversion applies stays covered; a lookahead year the provider
has not published yet is tolerated.
"""

import re
from html import unescape
from typing import Any, ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.service.ICS import (
    IcsFeedsParser,
    IcsSessionRetriever,
    resolve_select_option,
)
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://abfallkalender.regioit.de/kalender-wml"
_ORT = "Gronau"

# Restmüll, Bioabfall, Altpapier, Gelbe Tonne, Schadstoffmobil (all types
# offered by the calendar; matches the defaults preselected on the site).
_FRAKTIONEN = ["0", "3", "4", "5", "11"]

_STREET_LIST_RE = re.compile(r"streetList\s*=\s*\{(.*?)\};", re.DOTALL)
_STREET_ENTRY_RE = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:\s*(\d+)')


def _calendar_page(year: int, **_: Any) -> "dict[str, str]":
    return {
        "ort": _ORT,
        "jahr": str(year),
        "lang": "de",
        "format": "pdf",
        "zeit": "",
    }


def _street_id(response: Any, context: "dict[str, Any]") -> "dict[str, str]":
    """The configured street's id, read off the page's own street list."""
    streets: dict[str, str] = {}
    match = _STREET_LIST_RE.search(response.text)
    if match:
        for name, street_id in _STREET_ENTRY_RE.findall(match.group(1)):
            streets[unescape(name)] = street_id
    name = resolve_select_option("street", str(context["street"]), sorted(streets))
    return {"street_id": streets[name]}


def _download(year: int, street_id: str, **_: Any) -> "dict[str, Any]":
    return {
        "format": "ics",
        "zeit": "1:0:0",
        "jahr": str(year),
        "ort": _ORT,
        "strasse": street_id,
        "fraktion": _FRAKTIONEN,
    }


@final
class Source(BaseSource):
    TITLE = "Gronau"
    DESCRIPTION = "Source for Abfallkalender Gronau, Germany"
    URL = "https://abfallkalender.regioit.de/kalender-wml/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Viktoriastraße": {"street": "Viktoriastraße"},
        "Alter Markt": {"street": "Alter Markt"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "Nirgendwostraße"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau "
            "and pick your street; use the exact spelling shown there."
        ),
        "de": (
            "Öffnen Sie https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau "
            "und wählen Sie Ihre Straße; verwenden Sie die genaue Schreibweise."
        ),
    }

    PARAMS = (street(),)

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "url": f"{_BASE_URL}/index.jsp",
                "params": _calendar_page,
                "encoding": "utf-8",
                "extract": _street_id,
            }
        ],
        feed_url=f"{_BASE_URL}/downloadfile.jsp",
        feed_params=_download,
        encoding="utf-8",
        lookahead_month=10,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Bioabfall": wt.ORGANIC,
            "Altpapier": wt.PAPER,
            "Gelbe Tonne": wt.RECYCLABLES,
            "Schadstoffmobil in Ihrer Nähe": wt.HAZARDOUS,
        }
    )
