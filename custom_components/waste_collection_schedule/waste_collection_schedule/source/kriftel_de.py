"""Gemeinde Kriftel (Hesse, Germany).

Demonstrates ``IcsIndexRetriever``'s labelled selection where one feed serves
several names: Kriftel publishes one ICS file per *group* of collection
districts and year on its website ("Abfallkalender 2026 (1+3).ics" covers
districts 1 and 3), and regenerates each download link (with a fresh access
token in the query string) every year, so the current link is always
discovered rather than hardcoded. ``label`` returns every district a file
serves, and the user's district selects the file that carries it.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

_PAGE_URL = "https://www.kriftel.de/rathaus-politik/verwaltung/abfall/"

# Matches title text like "iCalendar-Datei „Abfallkalender 2026 (1+3).ics"
_CALENDAR_LINK_PATTERN = re.compile(r"Abfallkalender\s+\d{4}\s+\(([0-9+]+)\)\.ics")


_TYPE_VALUE_MAP = {
    "hausmüll": wt.GENERAL_WASTE,
    "biomüll": wt.ORGANIC,
    "blaue tonne": wt.PAPER,
    "gelber sack": wt.RECYCLABLES,
    "grünabfall": wt.GARDEN_WASTE,
    "schadstoffsammlung": wt.HAZARDOUS,
    "sperr- u. elektromüll": wt.BULKY_WASTE,
}


def _districts(anchor) -> list[str] | None:
    """The collection districts a download link serves, read off its title."""
    label = anchor.get("title") or anchor.get_text() or anchor["href"]
    match = _CALENDAR_LINK_PATTERN.search(label)
    if not match:
        return None
    return [district.strip() for district in match.group(1).split("+")]


@final
class Source(BaseSource):
    TITLE = "Gemeinde Kriftel"
    DESCRIPTION = "Source for Gemeinde Kriftel, Hesse, Germany waste collection."
    URL = "https://www.kriftel.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.HAZARDOUS,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "District 1": {"district": "1"},
        "District 2": {"district": "2"},
        "District 3": {"district": "3"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": "The Kriftel collection district your address belongs to: '1', '2' or '3'.",
        "de": "Der Krifteler Abfallbezirk, zu dem Ihre Adresse gehört: '1', '2' oder '3'.",
    }

    PARAMS = (text_field("district", "Collection district"),)

    retrieve = IcsIndexRetriever(
        index_url=_PAGE_URL,
        pattern=r"\.ics",
        label=_districts,
        argument="district",
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
