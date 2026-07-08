import html
import re
from datetime import date, timedelta
from typing import Optional

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Abfallwirtschaft Kyffhäuserkreis"
DESCRIPTION = (
    "Source for Abfallwirtschaft Kyffhäuserkreis, covering waste collection "
    "schedules for towns and villages within the Kyffhäuserkreis district, "
    "Thuringia, Germany."
)
URL = "https://abfall-kyffhaeuser.de"
COUNTRY = "de"

API_URL = "https://abfall-kyffhaeuser.de/wp-json/tribe/events/v1"

TEST_CASES = {
    "Ebeleben (single schedule)": {"city": "Ebeleben"},
    "Bad Frankenhausen - Tour 1": {"city": "Bad Frankenhausen - Tour 1"},
    "Sondershausen - Tour 3": {"city": "Sondershausen - Tour 3"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://abfall-kyffhaeuser.de/kalender/, open the 'Ort' filter "
        "and use the exact place name shown there as the 'city' argument. Larger "
        "towns (Bad Frankenhausen, Sondershausen, Artern) are split into several "
        "collection tours ('Tour 1', 'Tour 2', ...) - check your bin / waste "
        "collection notice or ask the Kyffhäuserkreis waste department which "
        "tour serves your street. If you enter an unknown or ambiguous name, "
        "the resulting error message will list the valid place names."
    ),
    "de": (
        "Besuchen Sie https://abfall-kyffhaeuser.de/kalender/, öffnen Sie den "
        "Filter 'Ort' und verwenden Sie den dort angezeigten Namen exakt als "
        "'city'-Parameter. Größere Orte (Bad Frankenhausen, Sondershausen, "
        "Artern) sind in mehrere Abfuhrtouren ('Tour 1', 'Tour 2', ...) "
        "aufgeteilt - bitte prüfen Sie Ihren Abfuhrkalender/-bescheid oder "
        "fragen Sie bei der Abfallwirtschaft Kyffhäuserkreis nach, welche Tour "
        "für Ihre Straße zuständig ist. Bei unbekannten oder mehrdeutigen "
        "Namen listet die Fehlermeldung alle gültigen Ortsnamen auf."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": (
            "Place name as shown in the 'Ort' filter on "
            "https://abfall-kyffhaeuser.de/kalender/, e.g. 'Ebeleben' or "
            "'Bad Frankenhausen - Tour 1'."
        ),
    },
    "de": {
        "city": (
            "Ortsname wie im Filter 'Ort' auf "
            "https://abfall-kyffhaeuser.de/kalender/ angezeigt, z. B. "
            "'Ebeleben' oder 'Bad Frankenhausen - Tour 1'."
        ),
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "Place / tour",
    },
    "de": {
        "city": "Ort / Tour",
    },
}


ICON_MAP = {
    "Restabfall": Icons.GENERAL_WASTE,
    "Biotonne": Icons.ORGANIC,
    "Papiertonne": Icons.PAPER,
    "Gelbe Tonne": Icons.PLASTIC_PACKAGING,
    "Gelber RC": Icons.PLASTIC_PACKAGING,
    "Weihnachtsbaum": Icons.CHRISTMAS_TREE,
}


def _normalize(value: str) -> str:
    value = html.unescape(value).strip().lower()
    value = value.translate(str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}))
    return re.sub(r"[^a-z0-9]", "", value)


class Source:
    def __init__(self, city: str):
        self._city = city
        self._session = requests.Session()

    def _get_all_venues(self) -> list[dict]:
        venues: list[dict] = []
        page = 1
        while True:
            r = self._session.get(
                f"{API_URL}/venues", params={"per_page": 100, "page": page}, timeout=30
            )
            r.raise_for_status()
            data = r.json()
            venues.extend(data.get("venues", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        return venues

    def _resolve_venue(self) -> int:
        venues = self._get_all_venues()
        target = _normalize(self._city)

        # exact match first
        for venue in venues:
            if _normalize(venue["venue"]) == target:
                return int(venue["id"])

        # fall back to substring match, e.g. "Bad Frankenhausen" matching all
        # of its "Tour" venues, so the user gets a helpful, narrowed-down list
        matches = [
            html.unescape(venue["venue"])
            for venue in venues
            if target in _normalize(venue["venue"])
        ]
        if not matches:
            matches = [html.unescape(venue["venue"]) for venue in venues]
        raise SourceArgumentNotFoundWithSuggestions("city", self._city, sorted(matches))

    def _get_all_events(self, venue_id: int) -> list[dict]:
        start_date = date.today()
        end_date = start_date + timedelta(days=400)
        events: list[dict] = []
        page = 1
        while True:
            r = self._session.get(
                f"{API_URL}/events",
                params={
                    "venue": venue_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "per_page": 50,
                    "page": page,
                },
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            events.extend(data.get("events", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        return events

    def fetch(self) -> list[Collection]:
        venue_id = self._resolve_venue()
        events = self._get_all_events(venue_id)

        entries = []
        for event in events:
            waste_type = str(event["title"])
            event_date = date.fromisoformat(str(event["start_date"])[:10])
            icon: Optional[Icons] = ICON_MAP.get(waste_type)
            entries.append(Collection(date=event_date, t=waste_type, icon=icon))
        return entries
