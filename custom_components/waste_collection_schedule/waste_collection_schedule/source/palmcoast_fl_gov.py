from datetime import datetime, timedelta

import requests

from ..collection import Collection
from ..exceptions import SourceArgumentNotFound

TITLE = "Palm Coast, FL"
DESCRIPTION = "Source for Palm Coast, FL waste collection."
URL = "https://www.palmcoast.gov"
COUNTRY = "us"

TEST_CASES = {
    "Ripcord Lane": {"street": "Ripcord Lane"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name (e.g. 'Ripcord Lane')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Name",
    },
}

API_URL = "https://www.palmcoast.gov/SalesforceDynamicForm/Schedule"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Yard Waste": "mdi:grass",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, street: str):
        self._street = street.strip()

    def fetch(self):
        session = requests.Session()

        # Make API request
        response = session.get(API_URL, params={"address": self._street}, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Check if request was successful
        if not data.get("success"):
            message = data.get("message", "Unknown error")
            raise SourceArgumentNotFound("street", self._street, message)

        # Get schedule data
        schedule_data = data.get("data", [])
        if not schedule_data:
            raise SourceArgumentNotFound(
                "street", self._street, "No schedule data found"
            )

        schedule = schedule_data[0]  # Take first result

        entries: list[Collection] = []

        # Parse solid waste days
        solid_waste_days = schedule.get("solidWasteDays", "")
        if solid_waste_days:
            entries.extend(self._parse_days(solid_waste_days, "Garbage"))

        # Parse yard waste days
        yard_waste_days = schedule.get("yardWasteDays", "")
        if yard_waste_days:
            entries.extend(self._parse_days(yard_waste_days, "Yard Waste"))

        # Parse recycling days
        recycle_days = schedule.get("recycleDays", "")
        if recycle_days:
            entries.extend(self._parse_days(recycle_days, "Recycling"))

        return entries

    def _parse_days(self, day_string: str, waste_type: str) -> list[Collection]:
        """Parse day string like 'Tuesday/Friday' and return Collection entries."""
        days = [day.strip() for day in day_string.split("/") if day.strip()]
        entries = []

        for day in days:
            if day in WEEKDAYS:
                entries.extend(self._weekly_dates(day, waste_type))

        return entries

    def _weekly_dates(self, day_name, waste_type):
        """Generate weekly collection dates for the given day and waste type."""
        weekday_idx = WEEKDAYS.get(day_name)
        if weekday_idx is None:
            return []

        today = datetime.now().date()
        days_ahead = (weekday_idx - today.weekday()) % 7
        next_date = today + timedelta(days=days_ahead)
        icon = ICON_MAP.get(waste_type)

        return [
            Collection(date=next_date + timedelta(weeks=i), t=waste_type, icon=icon)
            for i in range(26)
        ]
