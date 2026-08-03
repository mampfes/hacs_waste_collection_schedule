"""Coburg Entsorgungs- und Baubetrieb CEB (ceb-coburg.de).

Demonstrates ``IcsLookupRetriever``'s ``variants``: the street is resolved to
a path on the index page once, and the resolved path then serves *two* feeds,
this year (``getCalendarDates``) and next (``getCalendarDatesNextyear``),
which ``IcsFeedsParser`` merges and de-duplicates. The resolved key is a path
segment rather than a query argument, which is what ``feed_path`` takes a
callable for.

The classification mirrors the legacy source's substring match (a summary
containing "grün" is a green bin, etc.) via ``clean``, since the raw event
summaries are not exact matches for a canonical label or alias.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsLookupRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://abfuhrkalender.ceb-coburg.de/"

# The legacy source classified by substring, not exact match (e.g. a summary
# reading "Restmüll (Schwarze Tonne)" matches "schwarz"); the confusingly
# named bin colour is preserved exactly as before: the green bin -> paper.
_TYPE_VALUE_MAP = {
    "schwarz": wt.GENERAL_WASTE,
    "grün": wt.PAPER,
    "gelb": wt.RECYCLABLES,
}


def _clean(label: str) -> str:
    lowered = label.lower()
    for keyword in ("grün", "schwarz", "gelb"):
        if keyword in lowered:
            return keyword
    return label


def _street_path(lookup, source) -> str:
    """The index page's own path for the configured street."""
    soup = BeautifulSoup(lookup.text, "html.parser")
    street_map: dict[str, str] = {}
    streets_ul = soup.select_one("ul#mntc_streets")
    if streets_ul:
        for anchor in streets_ul.select("a.street[href]"):
            name = anchor.get_text(strip=True)
            href = anchor["href"]
            if name and href:
                street_map[name] = str(href)

    street_name = source.params["street"]
    if street_name not in street_map:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street_name, sorted(street_map.keys())
        )
    return street_map[street_name]


@final
class Source(BaseSource):
    TITLE = "Coburg Entsorgungs- und Baubetrieb CEB"
    DESCRIPTION = "Source for Coburg Entsorgungs- und Baubetrieb CEB."
    URL = "https://www.ceb-coburg.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Kanalstraße (Seite HUK)": {"street": "Kanalstraße, Seite HUK"},
        "Plattenäcker": {"street": "Plattenäcker"},
    }

    PARAMS = (street(),)
    RAISE_ON_EMPTY = True

    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP, clean=_clean)

    retrieve = IcsLookupRetriever(
        base_url=API_URL.rstrip("/"),
        lookup_path="/",
        extract=_street_path,
        feed_path=lambda key, **_: key,
        params=lambda variant, **_: {variant: 1},
        variants=("getCalendarDates", "getCalendarDatesNextyear"),
    )

    # The two feeds overlap around the year boundary, repeating collections.
    parse = IcsFeedsParser(parsers.IcsParser(), dedupe=True)
