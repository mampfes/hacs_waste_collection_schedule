import re
from datetime import date, datetime, timedelta
from typing import Literal, get_args

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsError,
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
)

TITLE = "City of Kalamunda"
DESCRIPTION = "Source for the City of Kalamunda rubbish collection."
URL = "https://www.kalamunda.wa.gov.au/kerbside-3-bin-system/collection-days/bin-day"
TEST_CASES = {
    "Kalamunda Hotel": {
        "suburb": "Kalamunda",
        "street_name": "Railway Road",
        "street_number": "43",
    },
    "Gooseberry Hill Multi-Use Facility": {
        "suburb": "Gooseberry hill",
        "street_name": "Ledger Road",
        "street_number": "42",
    },
    "High Wycombe Public Library": {
        "suburb": "High Wycombe",
        "street_name": "Markham Road",
        "street_number": "15",
    },
}

ICON_MAP = {
    "Red Lid Bin ( General Waste ) : Alternate Fortnight": "mdi:trash-can",
    "Yellow Lid Bin ( Recycling ) : Alternate Fortnight": "mdi:recycle",
    "Lime Green Lid Bin ( Green Waste FOGO ) : Every Week": "mdi:leaf",
}

SubUrbLiteral = Literal[
    "BICKLEY",
    "CANNING MILLS",
    "CARMEL",
    "FORRESTFIELD",
    "GOOSEBERRY HILL",
    "HACKETTS GULLY",
    "HIGH WYCOMBE",
    "KALAMUNDA",
    "LESMURDIE",
    "MAIDA VALE",
    "PAULLS VALLEY",
    "PICKERING BROOK",
    "PIESSE BROOK",
    "RESERVOIR",
    "WALLISTON",
    "WATTLE GROVE",
]

SUBURBS = get_args(SubUrbLiteral)


class Source:
    def __init__(self, suburb: SubUrbLiteral, street_name: str, street_number: str):
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

        # 2. Look for a recurring weekday: "Every Wednesday"
        day_match = re.search(
            r"every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            text,
            re.IGNORECASE,
        )
        if day_match:
            return self._get_next_weekday(day_match.group(1))

        return None

    def _extract_human_waste_name(self, name: str) -> str:
        """Extract a human friendly name for the waste type."""
        match = re.search(r"\((.*?)\)", name)
        if match:
            return match.group(1).strip()
        return name

    def fetch(self):

        config = MapsClientConfig(
            base_url="https://kalamunda.spatial.t1cloud.com",
            instance="spatial/intramaps",
            config_id="38999f30-1676-4524-b501-0130581a2ba2",
            project="d44a7973-329f-4626-9e09-35afeacc8724",
        )

        suburb_upper = self.suburb.upper()

        today = date.today()

        if suburb_upper not in SUBURBS:
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
        # NOTE: Search results always empty with suburb attached
        address = f"{self.street_number} {self.street_name}"
        entries = []

        try:
            with MapsClient(config) as client:
                data_dict = client.select_address(address, self.suburb)
                infoPanel = data_dict["response"]

                if not isinstance(infoPanel, dict):
                    raise IntraMapsSearchError(
                        f"Expected dict type in response field from address search but got {type(infoPanel)}"
                    )

                for waste_name, icon in ICON_MAP.items():
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

                    if matches:
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
                        search_strings = [raw_value, matches[0]["name"]]

                        for entry in search_strings:
                            if "fortnight" in entry.lower():
                                interval = 14
                            elif "week" in entry.lower():
                                interval = 7

                        # If recurring, add entries for 1 year (52 weeks)
                        if interval > 0:
                            # Calculate at least (two * interval) past events to ensure the Home Assistant calendar aligns correctly.
                            # This is necessary because the IntraMaps API only returns upcoming collection days, and Home Assistant
                            # may expect to see previous events to properly display recurring schedules and avoid gaps in the calendar.
                            current_date = start_date - timedelta(days=interval * 2)
                            # End date is 1 year from today
                            end_date = today + timedelta(days=365)

                            while current_date <= end_date:
                                entries.append(
                                    Collection(
                                        date=current_date,
                                        t=self._extract_human_waste_name(waste_name),
                                        icon=icon,
                                    )
                                )
                                current_date += timedelta(days=interval)
                        else:
                            # Single event (like Verge collection)
                            entries.append(
                                Collection(
                                    date=start_date,
                                    t=self._extract_human_waste_name(waste_name),
                                    icon=icon,
                                )
                            )

        except IntraMapsSearchError as e:
            raise SourceArgumentNotFound("street_name", self.street_name) from e
        except IntraMapsError as e:
            raise Exception(f"IntraMaps Operation Failed: {e}") from e
        except Exception as e:
            raise Exception(f"Unexpected System Error: {e}") from e

        return entries
