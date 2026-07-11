"""Coburg Entsorgungs- und Baubetrieb CEB (ceb-coburg.de).

Not a TwoStepRetriever shape: once the street is resolved to its path, the
legacy source fetches *two* schedule feeds against it (the current year via
``getCalendarDates`` and next year via ``getCalendarDatesNextyear``) and
merges them, rather than one lookup + one schedule fetch. A source-defined
``retrieve``/``parse`` pair covers the lookup + both feeds; the classification
mirrors the legacy source's substring match (a summary containing "grün" is a
green bin, etc.) via ``clean``, since the raw event summaries are not exact
matches for a canonical label or alias.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, PAPER, RECYCLABLES

API_URL = "https://abfuhrkalender.ceb-coburg.de/"

# The legacy source classified by substring, not exact match (e.g. a summary
# reading "Restmüll (Schwarze Tonne)" matches "schwarz"); the confusingly
# named bin colour is preserved exactly as before: the green bin -> paper.
_TYPE_VALUE_MAP = {
    "schwarz": GENERAL_WASTE,
    "grün": PAPER,
    "gelb": RECYCLABLES,
}


def _clean(label: str) -> str:
    lowered = label.lower()
    for keyword in ("grün", "schwarz", "gelb"):
        if keyword in lowered:
            return keyword
    return label


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

    def retrieve(self, source):
        street_name = source.params["street"]

        index = source.session.get(API_URL, timeout=30)
        index.raise_for_status()
        soup = BeautifulSoup(index.text, "html.parser")
        street_map: dict[str, str] = {}
        streets_ul = soup.select_one("ul#mntc_streets")
        if streets_ul:
            for a in streets_ul.select("a.street[href]"):
                name = a.get_text(strip=True)
                href = a["href"]
                if name and href:
                    street_map[name] = href

        if street_name not in street_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street_name, sorted(street_map.keys())
            )

        base_url = f"{API_URL.rstrip('/')}{street_map[street_name]}"
        return [
            source.session.get(base_url, params={"getCalendarDates": 1}, timeout=30),
            source.session.get(
                base_url, params={"getCalendarDatesNextyear": 1}, timeout=30
            ),
        ]

    def parse(self, responses, source=None):
        ics = ICS()
        events: dict[tuple, tuple] = {}
        for response in responses:
            response.raise_for_status()
            for date_, text in ics.convert(response.text):
                events[(date_, text)] = (date_, text)
        return sorted(events.values(), key=lambda event: event[0])

    def __init__(self, street: str):
        super().__init__(street=street)
