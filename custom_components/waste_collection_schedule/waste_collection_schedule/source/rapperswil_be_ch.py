"""Rapperswil (rapperswil-be.ch), Switzerland.

Demonstrates: a parameter-less, single-municipality source built with
``TwoStepRetriever`` -- the calendar page is scraped for its "icalTermine"
download link, which is then fetched directly. ``parse`` still needs a
source-defined override because the feed ships a malformed
``X-WR-TIMEZONE`` line that must be stripped before ``ICS`` can read it.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, PAPER

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

    def parse(self, response, source=None):
        text = response.text.replace("X-WR-TIMEZONE','EUROPE/BERLIN:", "")
        return ICS().convert(text)

    transform = ICSTransformer(
        type_value_map={
            "Hauskehricht": GENERAL_WASTE,
            "Grüngut": ORGANIC,
            "Papier und Karton": PAPER,
        }
    )

    def __init__(self):
        super().__init__()
