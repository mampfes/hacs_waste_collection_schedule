import re
from datetime import date, datetime, timedelta
from typing import Literal, get_args

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.RockinghamCityMaps import (
    IntraMapsError,
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
)

TITLE = "City of Rockingham"
DESCRIPTION = "Source for the City of Rockingham rubbish collection."
URL = "https://rockingham.wa.gov.au/your-services/waste-and-recycling/bin-collection"
TEST_CASES = {
    "IGA Baldivis Quarter": {
        "suburb": "Baldivis",
        "street_name": "Makybe Drive",
        "street_number": "59",
    },
    "The Warnbro Tavern": {
        "suburb": "Warnbro",
        "street_name": "Hokin Street",
        "street_number": "7",
    },
    "The Shoalwater Tavern": {
        "suburb": "Shoalwater",
        "street_name": "Second Avenue",
        "street_number": "62",
    },
}

WASTE_TYPES = {
    "Waste (Red Lid)": "mdi:trash-can",
    "Recycle (Yellow Lid)": "mdi:recycle",
    "FOGO Bin (FOGO lid)": "mdi:leaf",
    "Verge Collection Green Waste": "mdi:tree",
    "Verge Collection General": "mdi:sofa",
}

SubUrbLiteral = Literal[
    "BALDIVIS",
    "COOLOONGUP",
    "EAST ROCKINGHAM",
    "GARDEN ISLAND",
    "GOLDEN BAY",
    "HILLMAN",
    "KARNUP",
    "KERALUP",
    "PERON",
    "PORT KENNEDY",
    "ROCKINGHAM",
    "SAFETY BAY",
    "SECRET HARBOUR",
    "SHOALWATER",
    "SINGLETON",
    "WAIKIKI",
    "WARNBRO",
]

SUBURBS = get_args(SubUrbLiteral)


class Source:
    def __init__(self, suburb: SubUrbLiteral, street_name, street_number):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def _get_next_weekday(self, day_name):
        """Calculate the date of the next occurrence of a named day (e.g., 'Wednesday')."""
        days_of_week = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        target_day = days_of_week.index(day_name.lower())
        today = date.today()

        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:  # Target day has already happened this week
            days_ahead += 7

        return today + timedelta(days_ahead)

    def _parse_date(self, text):
        """Extract a specific date OR calculates the next occurrence of a weekday."""
        # 1. Look for a full date: "14 January 2026"
        match = re.search(r"(\d{1,2}\s+\w+\s+\d{4})", text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d %B %Y").date()
            except ValueError:
                pass

        # 2. Look for a recurring weekday: "on Wednesday"
        day_match = re.search(
            r"on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            text,
            re.IGNORECASE,
        )
        if day_match:
            return self._get_next_weekday(day_match.group(1))

        return None

    def fetch(self):

        config = MapsClientConfig(
            base_url="https://maps.rockingham.wa.gov.au",
            project="1917ad36-6a1d-4145-9eeb-736f8fa9646d",
        )

        self.suburb = self.suburb.upper()

        today = date.today()

        if self.suburb not in SUBURBS:
            raise SourceArgumentNotFoundWithSuggestions("suburb", self.suburb, SUBURBS)

        if self.street_number is None:
            raise SourceArgumentRequired(
                "street_number", "The street number can not be null"
            )

        if self.street_name is None:
            raise SourceArgumentRequired(
                "street_name", "The street name can not be null"
            )

        # Build the address string
        address = f"{self.street_number} {self.street_name} {self.suburb}"
        entries = []

        try:
            with MapsClient(config) as client:
                data_dict = client.select_address(address)
                infoPanel = data_dict["response"]

                for waste_name, icon in WASTE_TYPES.items():
                    # Safely navigate the tree; if any key is missing, it returns an empty list []
                    fields = (
                        infoPanel.get("infoPanels", {})
                        .get("info1", {})
                        .get("feature", {})
                        .get("fields", [])
                    )

                    matches = [
                        item for item in fields if item.get("name") == waste_name
                    ]

                    for match in matches:
                        # Get the first result, that's all we need
                        raw_value = matches[0]["value"]["value"]
                        if not raw_value:
                            continue

                        # Get the starting date
                        start_date = self._parse_date(raw_value)
                        if not start_date:
                            continue

                        # Determine frequency
                        interval = 0
                        if "weekly" in raw_value.lower():
                            interval = 7
                        elif "fortnightly" in raw_value.lower():
                            interval = 14

                        # If recurring, add entries for 1 year (52 weeks)
                        if interval > 0:
                            current_date = start_date
                            # End date is 1 year from today
                            end_date = today + timedelta(days=365)

                            while current_date <= end_date:
                                entries.append(
                                    Collection(
                                        date=current_date, t=waste_name, icon=icon
                                    )
                                )
                                current_date += timedelta(days=interval)
                        else:
                            # Single event (like Verge collection)
                            entries.append(
                                Collection(date=start_date, t=waste_name, icon=icon)
                            )

        except IntraMapsSearchError as e:
            raise Exception(f"No results found for address: {address}") from e
        except IntraMapsError as e:
            raise Exception(f"IntraMaps Operation Failed: {e}") from e
        except Exception as e:
            raise Exception(f"Unexpected System Error: {e}") from e

        return entries
