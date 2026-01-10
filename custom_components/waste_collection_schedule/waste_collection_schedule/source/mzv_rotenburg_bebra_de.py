from datetime import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from icalendar import Calendar
from typing import Any

TITLE = "MZV Rotenburg"
DESCRIPTION = "Source for MZV Rotenburg."
URL = "https://www.mzv-rotenburg-bebra.de"
TEST_CASES = {
    "Rotenburg an der Fulda 2 Ost": {
        "city": "rote",
        "yellow_route": "2",
        "paper_route": "Ost",
    }
}


ICON_MAP = {
    "Gelbe Tonne": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "Restabfall": "mdi:trash-can",
    "Papier": "mdi:package-variant",
    "Sperrmüll": "mdi:sofa",
    "Weiße Ware": "mdi:fridge",
    "Kühlgeräte": "mdi:fridge-outline",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "yellow_route": "Gelbe Tonne Rute",
        "paper_route": "Papier Rute",
    }
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "yellow_route": "Used if there are multiple routes for the yellow bin collection. E.g 'Rotenburg - Kernstadt' has yellow bin collection routes `1`,`2`,`3` and `4`.",
        "paper_route": "Used if there are multiple routes for the paper collection. E.g 'Rotenburg - Kernstadt' has paper collection routes `West` and `Ost`.",
        "city": "Should be spelled exactly like in the `ort` URL parameter of the link url shown on the website: https://www.mzv-rotenburg-bebra.de//webapp.html Like: `lisp`, `rot`, `bebra`, ...",
    },
    "de": {
        "city": "Genau wie in der `ort` URL-Parameter des Links auf der Website: https://www.mzv-rotenburg-bebra.de//webapp.html. Z.B. `lisp`, `rot`, `bebra`, ...",
        "yellow_route": "Wird verwendet, wenn es mehrere Routen für die Gelbe Tonne gibt. Z.B. hat 'Rotenburg - Kernstadt' Gelbe Tonne Routen `1`,`2`,`3` und `4`.",
        "paper_route": "Wird verwendet, wenn es mehrere Routen für die Papierabholung gibt. Z.B. hat 'Rotenburg - Kernstadt' Papierabholrouten `West` und `Ost`.",
    },
}


API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"


def ics_prop_to_str(value: Any) -> str:
    """
    Converts icalendar properties (vText, list[vText], None)
    into a clean UTF-8 string.
    """
    if not value:
        return ""

    if isinstance(value, list):
        return value[0].to_ical().decode("utf-8", errors="ignore")

    if hasattr(value, "to_ical"):
        return value.to_ical().decode("utf-8", errors="ignore")

    return str(value)


class Source:
    def __init__(
        self, city: str, yellow_route: str | None = None, paper_route: str | None = None
    ):
        self._city: str = city
        self._yellow_route: str | None = yellow_route
        self._paper_route: str | None = paper_route

    def _get_possible_cities(self) -> list[str]:
        r = requests.get(
            "https://www.mzv-rotenburg-bebra.de//webapp.html",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")
        links = soup.find_all(
            lambda tag: tag
            and tag.name == "a"
            and tag.get("href")
            and "entsorgung.php?ort=" in tag["href"]
        )
        return [link["href"].split("?ort=")[1] for link in links]

    def fetch(self) -> list[Collection]:
        args = {
            "ort": self._city,
        }
        r = requests.get(API_URL,
                         params=args,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        try:
            cal = Calendar.from_ical(r.text)
        except ValueError:
            try:
                cities = self._get_possible_cities()
            except Exception:
                raise SourceArgumentNotFound(
                    "city",
                    self._city,
                    "make sure the city is spelled exactly like in the link of the website https://www.mzv-rotenburg-bebra.de//webapp.html",
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "city",
                self._city,
                cities,
            )

        entries = []

        for component in cal.walk("VEVENT"):
            dtstart = component.get("DTSTART").dt
            if isinstance(dtstart, datetime):
                dtstart = dtstart.date()

            summary = component.get("SUMMARY")
            location = component.get("LOCATION")

            summary_text = ics_prop_to_str(summary).strip()
            location_text = ics_prop_to_str(location).strip()

            bin_type = summary_text.removeprefix("Entsorgung ").strip()
            bin_type_cmp = bin_type.lower()
            location_cmp = location_text.lower()

            if bin_type_cmp == "gelbe tonne" and self._yellow_route:
                if self._yellow_route.lower() not in location_cmp:
                    continue

            if bin_type_cmp == "papier" and self._paper_route:
                if self._paper_route.lower() not in location_cmp:
                    continue

            entries.append(
                Collection(
                    dtstart,
                    bin_type,
                    ICON_MAP.get(bin_type),
                )
            )

        return entries
