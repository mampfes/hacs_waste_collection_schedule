import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWB Abfallwirtschaft Vechta"
DESCRIPTION = "Source for AWB Abfallwirtschaft Vechta."
URL = "https://www.abfallwirtschaft-vechta.de/"
TEST_CASES = {
    "Vechta, An der Hasenweide": {"stadt": "Vechta", "strasse": "An der Hasenweide"},
    "Bakum, Up'n Sande": {"stadt": "Bakum", "strasse": "Up'n Sande"},
    "Neuenkirchen-Vörden, Braunschweiger Straße": {
        "stadt": "Neuenkirchen-Vörden",
        "strasse": "Braunschweiger Straße",
    },
    "Goldenstedt, An der Ellenbäke": {
        "stadt": "Goldenstedt",
        "strasse": "An der Ellenbäke",
    },
}


ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Glass": Icons.GLASS,
    "Bioabfall": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Altpapier Siemer": Icons.PAPER,
    "Altpapier Pamo": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Altkleider": Icons.TEXTILE,
    "Mobile Schadstoff.": Icons.HAZARDOUS,
}

BASE_URL = "https://www.abfallwirtschaft-vechta.de/index.php"
COMPONENT = "com_abfuhrkalender"
PAPIER_TYPES = ("pamo", "siemer")


class Source:
    def __init__(self, stadt: str, strasse: str):
        self._stadt: str = stadt
        self._strasse: str = strasse
        self._ics = ICS()
        self._session = requests.Session()
        self._street: dict | None = None

    def fetch(self) -> list[Collection]:
        if self._street is None:
            self._street = self._get_street(self._get_city_id())

        now = datetime.now()
        entries = self._get_data(now.year)
        if now.month == 12:
            try:
                entries += self._get_data(now.year + 1)
            except Exception:
                pass
        return entries

    def _get_city_id(self) -> int:
        r = self._session.get(
            BASE_URL, params={"option": COMPONENT, "view": "kalender"}
        )
        r.raise_for_status()
        match = re.search(
            r'<script[^>]*class="joomla-script-options[^"]*"[^>]*>(.*?)</script>',
            r.text,
            re.DOTALL,
        )
        if not match:
            raise ValueError("Could not find city list on abfallwirtschaft-vechta.de")
        cities = json.loads(match.group(1))[COMPONENT]["staedte"]

        for city in cities:
            if city["name"].casefold() == self._stadt.strip().casefold():
                return city["id"]
        raise SourceArgumentNotFoundWithSuggestions(
            "stadt", self._stadt, [c["name"] for c in cities]
        )

    def _get_street(self, city_id: int) -> dict:
        # The street search is a prefix search on the street name only, so strip a
        # possible " (Ortsteil)" suffix which is used to disambiguate streets.
        wanted = self._strasse.strip()
        query = re.sub(r"\s*\(.*\)\s*$", "", wanted)
        r = self._session.get(
            BASE_URL,
            params={
                "option": COMPONENT,
                "task": "proxy.strassen",
                "format": "json",
                "stadt": city_id,
                "q": query,
            },
        )
        r.raise_for_status()
        streets = r.json().get("data", [])

        def label(s: dict) -> str:
            return f"{s['name']} ({s['ortsteil']})" if s.get("ortsteil") else s["name"]

        matches = [s for s in streets if label(s).casefold() == wanted.casefold()]
        if not matches:
            matches = [s for s in streets if s["name"].casefold() == wanted.casefold()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "strasse", self._strasse, [label(s) for s in matches]
            )
        raise SourceArgumentNotFoundWithSuggestions(
            "strasse", self._strasse, [label(s) for s in streets]
        )

    def _get_data(self, jahr: int) -> list[Collection]:
        assert self._street is not None
        papier_types = [p for p in PAPIER_TYPES if self._street.get(p)] or [None]

        collection_entries: list[Collection] = []
        seen: set[tuple] = set()

        for papier_typ in papier_types:
            params = {
                "option": COMPONENT,
                "task": "proxy.ics",
                "strasse": self._street["id"],
                "jahr": jahr,
            }
            if papier_typ:
                params["papier"] = papier_typ

            r = self._session.get(BASE_URL, params=params)
            r.raise_for_status()
            r.encoding = "utf-8"

            # sometimes has a not ascii UID this would raise an Exception while converting
            dates = self._ics.convert(r.text.replace("UID:", "NOTUID: "))

            for d in dates:
                bin_type = (
                    d[1]
                    .replace("Abfuhrtermin", "")
                    .replace("Erinnerung", "")
                    .replace("für", "")
                    .strip()
                )

                if (d[0], bin_type) in seen:
                    continue
                seen.add((d[0], bin_type))

                collection_entries.append(
                    Collection(
                        d[0],
                        bin_type,
                        ICON_MAP.get(
                            re.sub("[0-9]", "", bin_type).strip().replace("  ", " ")
                        ),
                    )
                )
        return collection_entries
