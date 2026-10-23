import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Sector 27 - Datteln, Marl, Oer-Erkenschwick"
DESCRIPTION = "Source for Muellkalender in Kreis RE."
URL = "https://muellkalender.sector27.de"
TEST_CASES = {
    "Datteln": {"city": "Datteln", "street": "Am Bahnhof"},
    "Datteln Im Overkamp": {"city": "Datteln", "street": "Im Overkamp"},
    "Datteln range street": {
        "city": "Datteln",
        "street": "Ahsener Straße 113 - 161 (ungerade)",
    },
    "Marl": {"city": "Marl", "street": "Ahornweg"},
    "Oer-Erkenschick": {"city": "Oer-Erkenschwick", "street": "An der Zechenbahn"},
}

_LOGGER = logging.getLogger(__name__)

CITIES = {
    "Datteln": 9,
    "Marl": 3,
    "Oer-Erkenschwick": 8,
}

# The calendar marks each pickup with a coloured square only; there is no
# text label, so the waste type is derived from the square's colour class.
COLOR_TO_TYPE = {
    "bg-black": "Restmüll",
    "bg-yellow-700": "Bioabfall",
    "bg-blue-700": "Papier",
    "bg-yellow-400": "Gelbe Tonne",
}

ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Bioabfall": Icons.ORGANIC,
    "Papier": Icons.PAPER,
    "Gelbe Tonne": Icons.RECYCLING,
}

HEADERS = {"user-agent": "Mozilla/5.0"}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
    },
}


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street

    def _init_session(self):
        """Load the page and remember what Livewire needs for later updates."""
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        r = self._session.get(URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        livewire = soup.find("script", attrs={"data-update-uri": True})
        component = soup.find(attrs={"wire:name": "pickup-calendar"})
        if livewire is None or component is None:
            raise Exception("unexpected page layout on muellkalender.sector27.de")

        self._csrf = livewire["data-csrf"]
        self._update_uri = livewire["data-update-uri"]
        self._snapshot = component["wire:snapshot"]

    def _update(self, updates=None, calls=None):
        """Send a Livewire update and keep the returned component snapshot."""
        r = self._session.post(
            self._update_uri,
            json={
                "_token": self._csrf,
                "components": [
                    {
                        "snapshot": self._snapshot,
                        "updates": updates or {},
                        "calls": calls or [],
                    }
                ],
            },
            headers={"X-Livewire": "1", "X-CSRF-TOKEN": self._csrf},
        )
        r.raise_for_status()
        component = r.json()["components"][0]
        self._snapshot = component["snapshot"]
        return component["effects"]

    def _search_streets(self, search):
        effects = self._update(
            calls=[
                {
                    "path": "",
                    "method": "callSchemaComponentMethod",
                    "params": [
                        "form.street_id",
                        "getSearchResultsForJs",
                        {"search": search},
                    ],
                }
            ]
        )
        return effects["returns"][0]

    def _lookup_street_id(self):
        """Resolve the configured street name to its sector27 street id.

        The search returns at most 50 entries, so the full street name is
        tried first. If it does not match exactly, every word of the street
        name is searched as well to collect suggestions for the user.
        """
        if not self._street:
            raise SourceArgumentNotFound("street", self._street)

        target = self._street.strip().casefold()
        searches = [self._street.strip()]
        for token in self._street.split():
            if token not in searches:
                searches.append(token)

        suggestions: dict[str, None] = {}
        for search in searches:
            for entry in self._search_streets(search):
                name = entry.get("label", "").strip()
                if not name:
                    continue
                suggestions[name] = None
                if name.casefold() == target:
                    return entry["value"]

        if suggestions:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, list(suggestions.keys())
            )
        raise SourceArgumentNotFound("street", self._street)

    def _parse_calendar(self, html, year):
        soup = BeautifulSoup(html, "html.parser")
        entries = []

        months = soup.select("div.grid.grid-cols-7")
        if len(months) != 12:
            raise Exception(f"expected 12 months in calendar, found {len(months)}")

        for month, grid in enumerate(months, start=1):
            for cell in grid.find_all("div", class_="flex-col", recursive=False):
                day = None
                for child in cell.find_all("div", recursive=False):
                    if child.get_text(strip=True).isdigit():
                        day = int(child.get_text(strip=True))
                        break
                if day is None:
                    continue

                pickups = cell.find("div", class_="min-h-10")
                if pickups is None:
                    continue
                for marker in pickups.find_all("div", recursive=False):
                    color = next(
                        (c for c in marker.get("class", []) if c.startswith("bg-")),
                        None,
                    )
                    if color is None:
                        continue
                    waste_type = COLOR_TO_TYPE.get(color)
                    if waste_type is None:
                        _LOGGER.warning("unknown waste type colour %s", color)
                        waste_type = color
                    entries.append(
                        Collection(
                            datetime.date(year, month, day),
                            waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries

    def fetch(self):
        city_id = CITIES.get(self._city)
        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(CITIES.keys())
            )

        now = datetime.datetime.now()

        self._init_session()
        self._update({"data.city_id": city_id, "data.year": now.year})
        street_id = self._lookup_street_id()
        effects = self._update({"data.street_id": street_id})
        entries = self._parse_calendar(effects["html"], now.year)

        # from september on, also fetch next year
        if now.month > 8:
            effects = self._update({"data.year": now.year + 1})
            entries += self._parse_calendar(effects["html"], now.year + 1)

        return entries
