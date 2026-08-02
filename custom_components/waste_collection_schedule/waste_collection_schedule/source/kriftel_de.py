import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Gemeinde Kriftel"
DESCRIPTION = "Source for Gemeinde Kriftel, Hesse, Germany waste collection."
URL = "https://www.kriftel.de"
COUNTRY = "de"
TEST_CASES = {
    "District 1": {"district": "1"},
    "District 2": {"district": "2"},
    "District 3": {"district": "3"},
}

ICON_MAP = {
    "biomüll": Icons.BIO_KITCHEN,
    "blaue tonne": Icons.PAPER,
    "gelber sack": Icons.PLASTIC_PACKAGING,
    "grünabfall": Icons.GARDEN,
    "hausmüll": Icons.GENERAL_WASTE,
    "schadstoffsammlung": Icons.HAZARDOUS,
    "sperr- u. elektromüll": Icons.BULKY,
}

PAGE_URL = "https://www.kriftel.de/rathaus-politik/verwaltung/abfall/"

PARAM_TRANSLATIONS = {
    "de": {
        "district": "Bezirk",
    },
}
PARAM_DESCRIPTIONS = {
    "en": {
        "district": "The Kriftel collection district your address belongs to: "
        "'1', '2' or '3'",
    },
    "de": {
        "district": "Der Krifteler Abfallbezirk, zu dem Ihre Adresse gehört: "
        "'1', '2' oder '3'",
    },
}

# Matches title text like "iCalendar-Datei „Abfallkalender 2026 (1+3).ics"
CALENDAR_LINK_PATTERN = re.compile(r"Abfallkalender\s+\d{4}\s+\(([0-9+]+)\)\.ics")


class Source:
    def __init__(self, district: str):
        self._district: str = str(district).strip()
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        r = requests.get(PAGE_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Kriftel publishes one ICS calendar file per group of districts and
        # year on its website, and regenerates the download link (including a
        # fresh access token in the query string) every year, so we always
        # have to discover the current download link instead of hardcoding it.
        district_links: dict[str, str] = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".ics" not in href.lower():
                continue
            label = a.get("title") or a.get_text() or href
            match = CALENDAR_LINK_PATTERN.search(label)
            if not match:
                continue
            for district in match.group(1).split("+"):
                district_links[district.strip()] = href

        if self._district not in district_links:
            raise SourceArgumentNotFoundWithSuggestions(
                "district", self._district, list(district_links.keys())
            )

        entries = []
        href = district_links[self._district]
        r = requests.get(href)
        r.raise_for_status()
        r.encoding = "utf-8"  # requests doesn't guess the encoding correctly
        for date, summary in self._ics.convert(r.text):
            icon = ICON_MAP.get(summary.strip().lower())
            entries.append(Collection(date=date, t=summary, icon=icon))

        return entries
