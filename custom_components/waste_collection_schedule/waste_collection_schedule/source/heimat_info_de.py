import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Heimat-Info"
DESCRIPTION = "Source for Heimat-Info (heimat-info.de) waste collection schedules."
URL = "https://www.heimat-info.de"
COUNTRY = "de"

TEST_CASES = {
    "Gründau – Breitenborn": {
        "commune": "gruendau",
        "area": "Breitenborn",
    },
    "Gründau – Gettenbach": {
        "commune": "gruendau",
        "area": "Gettenbach",
    },
    "Salgen": {
        "commune": "salgen",
        "area": "Salgen",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "commune": "Commune (slug)",
        "area": "Collection area",
    },
    "de": {
        "commune": "Gemeinde (Slug)",
        "area": "Abholbereich",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "commune": "The URL slug of the commune on heimat-info.de (e.g. 'gruendau'). Find it in the URL https://www.heimat-info.de/gemeinden/<slug>/abfallkalender.",
        "area": "The name of the collection area / district (e.g. 'Breitenborn'). Leave empty if the commune has only one area.",
    },
    "de": {
        "commune": "Der URL-Slug der Gemeinde auf heimat-info.de (z. B. 'gruendau'). Zu finden in der URL https://www.heimat-info.de/gemeinden/<slug>/abfallkalender.",
        "area": "Der Name des Abholbereichs (z. B. 'Breitenborn'). Leer lassen, wenn die Gemeinde nur einen Bereich hat.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://www.heimat-info.de, search for your commune, and navigate to Abfallkalender. The commune slug is the part of the URL after '/gemeinden/'. If the calendar shows multiple collection areas, pick yours from the list.",
    "de": "Öffnen Sie https://www.heimat-info.de, suchen Sie Ihre Gemeinde und navigieren Sie zum Abfallkalender. Der Gemeinde-Slug ist der Teil der URL nach '/gemeinden/'. Falls der Kalender mehrere Abholbereiche zeigt, wählen Sie Ihren aus der Liste.",
}

ICON_MAP = {
    "Residual": "mdi:trash-can",
    "Organic": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recyclable": "mdi:recycle",
    "BulkyWaste": "mdi:sofa",
    "HazardousWaste": "mdi:biohazard",
}

API_BASE = "https://heimatinfo-api-platform.azurewebsites.net"

EXTRA_INFO = [
    {
        "title": "Aholfing",
        "url": "https://www.heimat-info.de/gemeinden/aholfing/abfallkalender",
        "country": "de",
        "default_params": {"commune": "aholfing"},
    },
    {
        "title": "Bellenberg",
        "url": "https://www.heimat-info.de/gemeinden/bellenberg/abfallkalender",
        "country": "de",
        "default_params": {"commune": "bellenberg"},
    },
    {
        "title": "Buch",
        "url": "https://www.heimat-info.de/gemeinden/buch/abfallkalender",
        "country": "de",
        "default_params": {"commune": "buch"},
    },
    {
        "title": "Eisingen",
        "url": "https://www.heimat-info.de/gemeinden/eisingen/abfallkalender",
        "country": "de",
        "default_params": {"commune": "eisingen"},
    },
    {
        "title": "Feichten a. d. Alz",
        "url": "https://www.heimat-info.de/gemeinden/feichten-alz/abfallkalender",
        "country": "de",
        "default_params": {"commune": "feichten-alz"},
    },
    {
        "title": "Gaimersheim",
        "url": "https://www.heimat-info.de/gemeinden/gaimersheim/abfallkalender",
        "country": "de",
        "default_params": {"commune": "gaimersheim"},
    },
    {
        "title": "Gemeinde Gründau",
        "url": "https://www.heimat-info.de/gemeinden/gruendau/abfallkalender",
        "country": "de",
        "default_params": {"commune": "gruendau"},
    },
    {
        "title": "Halsbach",
        "url": "https://www.heimat-info.de/gemeinden/halsbach/abfallkalender",
        "country": "de",
        "default_params": {"commune": "halsbach"},
    },
    {
        "title": "Hürtgenwald",
        "url": "https://www.heimat-info.de/gemeinden/hurtgenwald/abfallkalender",
        "country": "de",
        "default_params": {"commune": "hurtgenwald"},
    },
    {
        "title": "Kastl (Lkr. AÖ)",
        "url": "https://www.heimat-info.de/gemeinden/kastl/abfallkalender",
        "country": "de",
        "default_params": {"commune": "kastl"},
    },
    {
        "title": "Markt Kastl (Lauterachtal)",
        "url": "https://www.heimat-info.de/gemeinden/kastl-lauterachtal/abfallkalender",
        "country": "de",
        "default_params": {"commune": "kastl-lauterachtal"},
    },
    {
        "title": "Kirchweidach",
        "url": "https://www.heimat-info.de/gemeinden/kirchweidach/abfallkalender",
        "country": "de",
        "default_params": {"commune": "kirchweidach"},
    },
    {
        "title": "Kupferberg",
        "url": "https://www.heimat-info.de/gemeinden/kupferberg/abfallkalender",
        "country": "de",
        "default_params": {"commune": "kupferberg"},
    },
    {
        "title": "Loiching",
        "url": "https://www.heimat-info.de/gemeinden/loiching/abfallkalender",
        "country": "de",
        "default_params": {"commune": "loiching"},
    },
    {
        "title": "Oberrieden",
        "url": "https://www.heimat-info.de/gemeinden/oberrieden/abfallkalender",
        "country": "de",
        "default_params": {"commune": "oberrieden"},
    },
    {
        "title": "Oberroth",
        "url": "https://www.heimat-info.de/gemeinden/oberroth/abfallkalender",
        "country": "de",
        "default_params": {"commune": "oberroth"},
    },
    {
        "title": "Pastetten",
        "url": "https://www.heimat-info.de/gemeinden/pastetten/abfallkalender",
        "country": "de",
        "default_params": {"commune": "pastetten"},
    },
    {
        "title": "Pfaffenhausen",
        "url": "https://www.heimat-info.de/gemeinden/pfaffenhausen/abfallkalender",
        "country": "de",
        "default_params": {"commune": "pfaffenhausen"},
    },
    {
        "title": "Roggenburg",
        "url": "https://www.heimat-info.de/gemeinden/roggenburg/abfallkalender",
        "country": "de",
        "default_params": {"commune": "roggenburg"},
    },
    {
        "title": "Röttenbach",
        "url": "https://www.heimat-info.de/gemeinden/rottenbach/abfallkalender",
        "country": "de",
        "default_params": {"commune": "rottenbach"},
    },
    {
        "title": "Salgen",
        "url": "https://www.heimat-info.de/gemeinden/salgen/abfallkalender",
        "country": "de",
        "default_params": {"commune": "salgen"},
    },
    {
        "title": "Schäftlarn",
        "url": "https://www.heimat-info.de/gemeinden/schaftlarn/abfallkalender",
        "country": "de",
        "default_params": {"commune": "schaftlarn"},
    },
    {
        "title": "Trausnitz",
        "url": "https://www.heimat-info.de/gemeinden/trausnitz/abfallkalender",
        "country": "de",
        "default_params": {"commune": "trausnitz"},
    },
    {
        "title": "Unterroth",
        "url": "https://www.heimat-info.de/gemeinden/unterroth/abfallkalender",
        "country": "de",
        "default_params": {"commune": "unterroth"},
    },
    {
        "title": "Wutach",
        "url": "https://www.heimat-info.de/gemeinden/wutach/abfallkalender",
        "country": "de",
        "default_params": {"commune": "wutach"},
    },
]


class Source:
    def __init__(self, commune: str, area: str | None = None):
        self._commune = commune.strip().lower()
        self._area = area.strip() if area else None

    def fetch(self) -> list[Collection]:
        # Fetch all pickup areas for this commune
        r = requests.get(
            f"{API_BASE}/communes/{self._commune}/garbagepickupareas",
            timeout=30,
        )
        if r.status_code == 404:
            raise SourceArgumentNotFound("commune", self._commune)
        r.raise_for_status()

        areas = r.json()
        if not areas:
            raise SourceArgumentNotFound("commune", self._commune)

        # Resolve requested area
        if self._area is None:
            if len(areas) == 1:
                area_id = areas[0]["id"]
            else:
                area_names = [a["name"] for a in areas]
                raise SourceArgumentNotFoundWithSuggestions(
                    "area",
                    "",
                    area_names,
                )
        else:
            match = next(
                (a for a in areas if a["name"].lower() == self._area.lower()), None
            )
            if match is None:
                area_names = [a["name"] for a in areas]
                raise SourceArgumentNotFoundWithSuggestions(
                    "area", self._area, area_names
                )
            area_id = match["id"]

        # Fetch pickup dates for the resolved area
        r2 = requests.get(
            f"{API_BASE}/communes/{self._commune}/garbagepickupareas/{area_id}/garbagepickupdates",
            timeout=30,
        )
        r2.raise_for_status()

        entries: list[Collection] = []
        for item in r2.json():
            date = datetime.datetime.fromisoformat(
                item["date"].replace("Z", "+00:00")
            ).date()
            waste_type: str = item["type"]
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
