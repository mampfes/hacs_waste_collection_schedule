import re
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

TITLE = "Northern Beaches Council (NSW)"
DESCRIPTION = "Source for Northern Beaches Council waste collection."
URL = "https://www.northernbeaches.nsw.gov.au"
TEST_CASES = {
    "Manly": {"address": "25 Pittwater Road MANLY"},
    "Brookvale": {"address": "25 Old Pittwater Road BROOKVALE"},
    "Dee Why": {"address": "10 Howard Avenue DEE WHY"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Organics": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your address as shown on the Northern Beaches Council website, e.g. '25 Pittwater Road MANLY'.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your street address including suburb in uppercase, e.g. '25 Pittwater Road MANLY'.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

SEARCH_URL = "https://pubapp.northernbeaches.nsw.gov.au/waste/waste.ashx"
SCHEDULE_URL = "https://pubapp.northernbeaches.nsw.gov.au/waste/wastesearch.ashx"
HEADERS = {"User-Agent": "Mozilla/5.0"}

MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        # Step 1: Search for address via autocomplete endpoint
        r = requests.get(
            SEARCH_URL,
            params={"term": self._address},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        results = r.json()

        if not results:
            raise SourceArgumentNotFound("address", self._address)

        # Try exact match first (case-insensitive)
        property_id = None
        for result in results:
            if result["value"].lower() == self._address.lower():
                property_id = result["id"]
                break

        if property_id is None:
            if len(results) == 1:
                # Single result - use it
                property_id = results[0]["id"]
            else:
                # Multiple matches, none exact - provide suggestions
                suggestions = [entry["value"] for entry in results]
                raise SourceArgAmbiguousWithSuggestions(
                    "address", self._address, suggestions
                )

        # Step 2: Get collection schedule HTML
        r = requests.post(
            SCHEDULE_URL,
            data={"property": property_id},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        html = r.text

        if "ERROR" in html:
            raise Exception(
                f"Northern Beaches API returned an error for property {property_id}"
            )

        # Step 3: Parse next collection date from HTML
        # Format: <strong>Wednesday, 8 April</strong>
        date_match = re.search(r"<strong>\w+day,?\s+(\d{1,2})\s+(\w+)</strong>", html)
        if not date_match:
            raise Exception("Could not parse collection date from response")

        day_num = int(date_match.group(1))
        month_name = date_match.group(2).lower()
        month_num = MONTH_MAP.get(month_name)
        if not month_num:
            raise Exception(f"Unknown month in response: {date_match.group(2)}")

        today = date.today()
        try:
            next_date = date(today.year, month_num, day_num)
        except ValueError as e:
            raise Exception(
                f"Invalid date in response: {day_num} {date_match.group(2)}"
            ) from e

        # If the parsed date is far in the past, it must be next year
        if next_date < today - timedelta(days=30):
            next_date = date(today.year + 1, month_num, day_num)

        # Step 4: Detect A/B zone from the PDF calendar link.
        # The API response contains a link like ".../ThursdayB.pdf" which
        # encodes the collection zone. B zones have the opposite fortnightly
        # alternation from A zones.
        zone_match = re.search(r"bin-collection-days/\w+([AB])\.pdf", html)
        is_b_zone = zone_match and zone_match.group(1) == "B"

        # Step 5: Generate collection entries for ~6 months.
        # Northern Beaches pattern:
        #   - General Waste: weekly
        #   - Recycling & Garden Organics: fortnightly, alternating weeks
        # Use ISO week number as a stable anchor for the alternation:
        #   B zones: even ISO weeks = Recycling, odd = Garden Organics
        #   A zones: even ISO weeks = Garden Organics, odd = Recycling
        entries: list[Collection] = []

        for week in range(26):
            d = next_date + timedelta(weeks=week)
            iso_week = d.isocalendar()[1]
            even_week = iso_week % 2 == 0

            entries.append(
                Collection(
                    date=d,
                    t="General Waste",
                    icon=ICON_MAP.get("General Waste"),
                )
            )

            recycling_week = even_week if is_b_zone else not even_week

            if recycling_week:
                entries.append(
                    Collection(
                        date=d,
                        t="Recycling",
                        icon=ICON_MAP.get("Recycling"),
                    )
                )
            else:
                entries.append(
                    Collection(
                        date=d,
                        t="Garden Organics",
                        icon=ICON_MAP.get("Garden Organics"),
                    )
                )

        return entries
