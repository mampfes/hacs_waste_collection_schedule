import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Gemeinde Maur"
DESCRIPTION = "Source for waste collection in Maur, Canton of Zurich, Switzerland."
URL = "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html"
COUNTRY = "ch"

TEST_CASES: dict[str, dict] = {
    "Maur": {},
}

ICON_MAP = {
    "Grüngut": Icons.ORGANIC,
    "Grüngut/Christbaum": Icons.ORGANIC,
    "Kehricht": Icons.GENERAL_WASTE,
    "Karton": Icons.PAPER,
    "Papiersammlung": Icons.PAPER,
    "Sonderabfall": Icons.HAZARDOUS,
    "Häcksel-Service": Icons.GARDEN,
    "Metall": Icons.RECYCLING,
    "Hauptsammelstelle": Icons.RECYCLING,
}

TERMINE_URL = (
    "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html/924"
)

# The event list is paginated; page 1 is the bare URL, further pages use this suffix.
PAGE_SUFFIX = "/eventsjsRequest/0/eventspage/{page}"

# Safety limit so a website change can never turn the pagination loop into an
# unbounded number of requests.
MAX_PAGES = 25

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
        """Normalize waste type names for icon mapping.

        Maps all chipping service variants (Häcksel-Service, Häckseldienst) to
        'Häcksel-Service' and all collection point variants to 'Hauptsammelstelle'.
        The provider appends dates and district names to these titles, so without
        normalization every year would introduce a brand new waste type.
        """
        waste_type_lower = waste_type.lower()

        if "häcksel" in waste_type_lower:
            return "Häcksel-Service"

        if "hauptsammelstelle" in waste_type_lower:
            return "Hauptsammelstelle"

        return waste_type

    def _parse_german_date(self, date_str: str) -> date | None:
        """Parse a German date string like '15. September 2026' or '5. März 2026'."""
        clean_str = re.sub(r"<[^>]+>", "", date_str).strip()

        match = re.match(r"(\d{1,2})\.\s*([A-Za-zäöüß]+)\s+(\d{4})", clean_str)
        if not match:
            return None

        month_num = GERMAN_MONTHS.get(match.group(2))
        if not month_num:
            return None

        return datetime(int(match.group(3)), month_num, int(match.group(1))).date()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        entries: list[Collection] = []
        seen: set[tuple[date, str]] = set()
        found_any_event = False

        for page in range(1, MAX_PAGES + 1):
            url = (
                TERMINE_URL
                if page == 1
                else TERMINE_URL + PAGE_SUFFIX.format(page=page)
            )

            r = session.get(url, timeout=30)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")

            # Each event is a li with class 'mod-entry event-item'
            event_items = soup.select("li.mod-entry.event-item")
            if not event_items:
                # An empty page marks the end of the paginated list.
                break

            found_any_event = True

            for item in event_items:
                # Extract waste type from the h2 > a tag
                type_link = item.select_one(
                    "h2.mod-entry-title.event-title.summary > a"
                )
                if not type_link:
                    continue

                waste_type = type_link.get_text(strip=True)
                if not waste_type:
                    continue

                normalized_type = self._normalize_waste_type(waste_type)

                # The datetime attribute holds the start of the recurring series,
                # not the occurrence, so the visible text has to be parsed instead.
                time_tag = item.select_one("time.dtstart")
                if not time_tag:
                    continue

                collection_date = self._parse_german_date(time_tag.get_text(strip=True))
                if not collection_date:
                    continue

                key = (collection_date, normalized_type)
                if key in seen:
                    continue
                seen.add(key)

                entries.append(
                    Collection(
                        date=collection_date,
                        t=normalized_type,
                        icon=ICON_MAP.get(normalized_type),
                    )
                )

        if not found_any_event:
            raise ValueError(
                "No waste collection events found. The website structure may have changed."
            )

        if not entries:
            raise ValueError(
                "No valid waste collection dates could be extracted. "
                "The website structure may have changed."
            )

        return entries
