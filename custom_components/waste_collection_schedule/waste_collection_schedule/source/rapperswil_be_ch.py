"""Rapperswil (rapperswil-be.ch), Switzerland.

Demonstrates: a parameter-less, single-municipality source built with
``TwoStepRetriever`` -- the calendar page is scraped for its "icalTermine"
download link, which is then fetched directly.

The feed ships a malformed ``X-WR-TIMEZONE`` property line that used to abort
the whole parse. That is now repaired inside the shared converter
(``service.ICS._drop_malformed_content_lines``), so any provider with a broken
property line is covered, not just this one.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.rapperswil-be.ch"
_API_URL = f"{_BASE_URL}/de/abfallwirtschaft/abfallkalender/"


def _pick_ics_url(lookup, source) -> str:
    soup = BeautifulSoup(lookup.text, "html.parser")
    ical_div = soup.select_one("div#icalTermine")
    if ical_div is None:
        raise ValueError("No icalTermine found")
    link = ical_div.select_one("a")
    if link is None:
        raise ValueError("No ical link found")

    href = link["href"]
    if not isinstance(href, str):
        raise ValueError("No href found")

    if href.startswith("/"):
        return _BASE_URL + href
    if not href.startswith("http"):
        return _API_URL + href
    return href


@final
class Source(BaseSource):
    TITLE = "Rapperswil"
    DESCRIPTION = "Source for Rapperswil."
    URL = "https://www.rapperswil-be.ch/"
    COUNTRY = "ch"

    TEST_CASES: ClassVar[dict] = {
        "Rapperswil": {},
    }

    retrieve = TwoStepRetriever(
        lookup_url=_API_URL,
        extract=_pick_ics_url,
        schedule_url=lambda key, **_: key,
    )
    parse = parsers.IcsParser()

    transform = ICSTransformer(
        type_value_map={
            "Hauskehricht": wt.GENERAL_WASTE,
            "Grüngut": wt.ORGANIC,
            "Papier und Karton": wt.PAPER,
        }
    )
