from __future__ import annotations

from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Orange County, FL"
DESCRIPTION = "Source for Orange County Government curbside collection schedules."
URL = "https://ocarcims.ocfl.net/"
COUNTRY = "us"

TEST_CASES = {
    "Orange County Fire Station 27": {"parcel_id": "012128690001243"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "parcel_id": "15-digit parcel ID from the Orange County Property Appraiser (ocpafl.org)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "parcel_id": "Parcel ID",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your address at https://ocarcims.ocfl.net/ or https://www.ocpafl.org/. "
        "The 15-digit parcel ID appears in the search results on either site."
    ),
}

DEFAULT_SOURCE = "https://ocarcims.ocfl.net/Home.aspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycle": Icons.RECYCLING,
    "Recycling": Icons.RECYCLING,
    "Yard Waste": Icons.GARDEN,
    "Bulk": Icons.BULKY,
    "Large Item": Icons.BULKY,
}


class Source:
    def __init__(self, parcel_id: str):
        self._parcel_id = str(parcel_id).strip()

    def fetch(self) -> list[Collection]:
        if not self._parcel_id:
            raise SourceArgumentNotFound("parcel_id", self._parcel_id)

        response = requests.get(
            DEFAULT_SOURCE,
            params={"ParcelID": self._parcel_id},
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        result = parse_lookup_result(response.text)
        if not result:
            raise SourceArgumentNotFound("parcel_id", self._parcel_id)

        entries: list[Collection] = []
        for item in result:
            service = item.get("service", "")
            day = item.get("day", "")
            for d in _upcoming_dates(day, weeks=8):
                entries.append(
                    Collection(
                        date=d,
                        t=service,
                        icon=ICON_MAP.get(service, Icons.GENERAL_WASTE),
                    )
                )

        return entries


_SKIP_PREFIXES = {"current collection schedule", "parcel id", "owner", "address"}


def parse_lookup_result(html: str) -> list[dict[str, str]]:
    """Extract the pickup schedule from the result HTML."""
    soup = BeautifulSoup(html, "html.parser")

    schedule: list[dict[str, str]] = []
    pickup_panel = soup.find(id="Curbside_PickupResultsUpdatePanel")
    if pickup_panel:
        for table in pickup_panel.find_all("table"):
            for row in table.find_all("tr"):
                cells = [
                    cell.get_text(" ", strip=True)
                    for cell in row.find_all(["td", "th"])
                ]
                if len(cells) >= 2:
                    first = cells[0].strip()
                    day = cells[1].strip()
                    lower = first.lower()
                    if first and not any(lower.startswith(p) for p in _SKIP_PREFIXES):
                        schedule.append({"service": first, "day": day})

    return schedule


_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _parse_day(day: str) -> date | None:
    """Parse a collection day into a date.

    Accepts bare weekday names ('Monday') — returns the next occurrence —
    or explicit date strings ('Mon 05/20/2024', '2024-05-20').
    """
    if not day:
        return None

    lower = day.strip().lower()
    if lower in _WEEKDAYS:
        today = date.today()
        days_ahead = (_WEEKDAYS[lower] - today.weekday()) % 7 or 7
        return today + timedelta(days=days_ahead)

    for fmt in ("%a %m/%d/%Y", "%A %m/%d/%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(day, fmt).date()
        except ValueError:
            continue
    return None


def _upcoming_dates(day: str, weeks: int = 8) -> list[date]:
    """Return the next ``weeks`` occurrences of a collection day."""
    first = _parse_day(day)
    if first is None:
        return []
    return [first + timedelta(weeks=i) for i in range(weeks)]
