import re
from datetime import date, datetime
from typing import Optional

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Fuquay-Varina, North Carolina"
DESCRIPTION = "Source for Fuquay-Varina, NC waste collection via ArcGIS services"
URL = "https://gis1.fuquay-varina.org/"
TEST_CASES = {
    "Test_001": {"street_address": "155 S Main St"},
    "Test_002": {"street_address": "123 E Vance St"},
}

API_URL = "https://gis1.fuquay-varina.org/server/rest/services/Public/Solid_Waste_Information/MapServer/0/query"

ICON_MAP = {
    "GARBAGE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
}


class Source:
    def __init__(self, street_address: str):
        self._street_address = street_address.strip()

    def fetch(self) -> list[Collection]:
        # Clean and format the address for the query
        address_query = self._street_address.lower().strip()

        params = {
            "f": "json",
            "where": f"LOWER(ADDRESS) LIKE '%{address_query}%'",
            "outFields": "garbage_next_pickup_date,recycling_next_pickup_date",
        }

        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if not data.get("features"):
            raise Exception("Address not found or no collection data available")

        # Get the first matching feature
        feature = data["features"][0]
        attributes = feature["attributes"]

        entries = []

        # Parse garbage collection
        garbage_date_text = attributes.get("garbage_next_pickup_date", "")
        if garbage_date_text:
            garbage_date = self._parse_date_from_text(garbage_date_text)
            if garbage_date:
                entries.append(
                    Collection(date=garbage_date, t="Garbage", icon=ICON_MAP["GARBAGE"])
                )

        # Parse recycling collection
        recycling_date_text = attributes.get("recycling_next_pickup_date", "")
        if recycling_date_text:
            recycling_date = self._parse_date_from_text(recycling_date_text)
            if recycling_date:
                entries.append(
                    Collection(
                        date=recycling_date, t="Recycling", icon=ICON_MAP["RECYCLING"]
                    )
                )

        return entries

    def _parse_date_from_text(self, date_text: str) -> Optional[date]:
        """Parse date from text like 'The next garbage pickup date for this address is Monday, January 06'."""
        if not date_text:
            return None

        # Use regex to extract month and day
        # Pattern matches: "January 06", "February 15", etc.
        match = re.search(r"([A-Za-z]+),?\s+(\d{1,2})", date_text)
        if not match:
            return None

        month_name = match.group(1)
        day = int(match.group(2))

        # Convert month name to number
        month_map = {
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

        month = month_map.get(month_name.lower())
        if not month:
            return None

        # Determine the year - handle year boundary cases
        current_date = datetime.now().date()
        current_year = current_date.year

        try:
            pickup_date = datetime(current_year, month, day).date()

            # If the pickup date is more than 60 days in the past, it's probably next year
            # This handles Dec->Jan transitions while allowing for API update delays
            if (current_date - pickup_date).days > 60:
                pickup_date = datetime(current_year + 1, month, day).date()

            return pickup_date
        except ValueError:
            # Invalid date (like February 30)
            return None
