import requests
from bs4 import BeautifulSoup
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Coburg Entsorgungs- und Baubetrieb CEB"
DESCRIPTION = "Source for Coburg Entsorgungs- und Baubetrieb CEB."
URL = "https://www.ceb-coburg.de/"
TEST_CASES = {
    "Kanalstraße (Seite HUK)": {"street": "Kanalstraße, Seite HUK"},
    "Plattenäcker": {"street": "Plattenäcker"},
}

ICON_MAP = {
    "Schwarz": "mdi:trash-can",
    "Grün": "mdi:package-variant",
    "Gelb": "mdi:recycle",
}

API_URL = "https://abfuhrkalender.ceb-coburg.de/"


class Source:
    def __init__(self, street: str):
        self._street: str = street
        self._ics = ICS()

    def _get_supported_street_map(self) -> dict[str, str]:
        r = requests.get(API_URL, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        streets: dict[str, str] = {}

        streets_ul = soup.select_one("ul#mntc_streets")
        if not streets_ul:
            return streets

        for a in streets_ul.select("a.street[href]"):
            name = a.get_text(strip=True)
            href = a["href"]
            if name and href:
                streets[name] = href

        return streets

    def _create_collection(self, d, text: str) -> Collection:
        s = text.lower()

        if "grün" in s:
            t = "Grün"
        elif "schwarz" in s:
            t = "Schwarz"
        elif "gelb" in s:
            t = "Gelb"
        else:
            t = text.strip()

        return Collection(
            date=d,
            t=t,
            icon=ICON_MAP.get(t),
        )

    def fetch(self) -> list[Collection]:
        street_map = self._get_supported_street_map()

        if self._street not in street_map:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                sorted(street_map.keys()),
            )

        street_path = street_map[self._street]
        base_url = f"{API_URL.rstrip('/')}{street_path}"

        entries: list[Collection] = []

        for param in ("getCalendarDates", "getCalendarDatesNextyear"):
            r = requests.get(base_url, params={param: 1}, timeout=30)
            r.raise_for_status()

            dates = self._ics.convert(r.text)

            for d, text in dates:
                entries.append(self._create_collection(d, text))

        if not entries:
            raise SourceArgumentNotFound("street", self._street)

        unique = {(e.date, e.type): e for e in entries}
        return sorted(unique.values(), key=lambda e: e.date)
