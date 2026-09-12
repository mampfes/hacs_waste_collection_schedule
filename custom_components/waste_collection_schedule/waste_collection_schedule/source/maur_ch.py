import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Gemeinde Maur"
DESCRIPTION = "Source for waste collection in Maur, Canton of Zurich, Switzerland."
URL = "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html"
COUNTRY = "ch"

TEST_CASES = {
    "Maur": {},
}

ICON_MAP = {
    "Grüngut": Icons.ORGANIC,
    "Kehricht": Icons.GENERAL_WASTE,
    "Karton": Icons.PAPER,
    "Sonderabfall": Icons.HAZARDOUS,
    "Häcksel-Service": Icons.GARDEN,
    "Häckseldienst": Icons.GARDEN,
    "Hauptsammelstelle": Icons.RECYCLING,
    "Hauptsammelstelle Werkhof Ebmatingen offener Samstag": Icons.RECYCLING,
    "Häcksel-Service ab 19. Oktober 2026 - in Ebmatingen, Maur, Uessikon": Icons.GARDEN,
}

TERMINE_URL = "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html/924"

# German month names for date parsing
GERMAN_MONTHS = {
    "Januar": 1,
    "Februar": 2,
    "März": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


class Source:
    def __init__(self):
        # No parameters needed - Maur has common dates for the entire municipality
        pass

    def _normalize_waste_type(self, waste_type: str) -> str:
        """Normalize waste type names for icon mapping."""
        # Handle long names by extracting the main type
        if "Häcksel" in waste_type or "Häckseldienst" in waste_type:
            return "Häcksel-Service"
        if "Hauptsammelstelle" in waste_type:
            return "Hauptsammelstelle"
        return waste_type

    def _parse_german_date(self, date_str: str) -> tuple[int, int, int] | None:
        """Parse a German date string like '15. September 2026' or '5. März 2026'."""
        # Remove any HTML tags or extra whitespace
        clean_str = re.sub(r"<[^>]+>", "", date_str).strip()

        # Match pattern: day. Month Year
        match = re.match(r"(\d{1,2})\.\s*([A-Za-zäöüß]+)\s+(\d{4})", clean_str)
        if not match:
            return None

        day = int(match.group(1))
        month_german = match.group(2)
        year = int(match.group(3))

        # Convert German month name to number
        month_num = GERMAN_MONTHS.get(month_german)
        if not month_num:
            return None

        return (year, month_num, day)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        r = session.get(TERMINE_URL, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []

        # Find all event items - each is in a li with class 'mod-entry event-item'
        event_items = soup.select("li.mod-entry.event-item")

        if not event_items:
            raise ValueError(
                "No waste collection events found. The website structure may have changed."
            )

        for item in event_items:
            # Extract waste type from the h2 > a tag
            type_link = item.select_one("h2.mod-entry-title.event-title.summary > a")
            if not type_link:
                continue

            waste_type = type_link.get_text(strip=True)
            if not waste_type:
                continue

            # Normalize the waste type for icon mapping
            normalized_type = self._normalize_waste_type(waste_type)

            # Extract date from the time tag
            time_tag = item.select_one("time.dtstart")
            if not time_tag:
                continue

            date_str = time_tag.get_text(strip=True)
            parsed_date = self._parse_german_date(date_str)
            if not parsed_date:
                continue

            year, month, day = parsed_date
            date_obj = datetime(year, month, day).date()

            entries.append(
                Collection(
                    date=date_obj,
                    t=waste_type,
                    icon=ICON_MAP.get(normalized_type),
                )
            )

        if not entries:
            raise Exception(
                "No valid waste collection dates could be extracted. "
                "The website structure may have changed."
            )

        return entries
