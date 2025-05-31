import datetime
import logging
from typing import Any

from dateutil.rrule import MO, TU, WE, TH, rrule, WEEKLY
from dateutil.parser import parse
from waste_collection_schedule import Collection

TITLE = "Delta BC Canada Waste Collection"
DESCRIPTION = "Source for Delta BC waste collection schedule"
URL = "https://delta.ca"

# Test cases for each zone
TEST_CASES = {
    "Green Zone": {"zone": "GREEN"},
    "Blue Zone": {"zone": "BLUE"},
    "Red Zone": {"zone": "RED"},
    "Yellow Zone": {"zone": "YELLOW"},
}

ZONES = {
    "GREEN": {"day": MO, "name": "Green Zone (Tsawwassen) - Monday"},
    "BLUE": {"day": TU, "name": "Blue Zone (Ladner) - Tuesday"},
    "RED": {"day": WE, "name": "Red Zone (North Delta 1) - Wednesday"},
    "YELLOW": {"day": TH, "name": "Yellow Zone (North Delta 2) - Thursday"},
}

# Holiday exceptions - collection will be delayed
# Format: "YYYY-MM-DD" for specific years
HOLIDAY_EXCEPTIONS = [
    "2025-01-01",  # January 1, 2025
    "2025-02-17",  # February 17, 2025
    "2025-04-21",  # April 21, 2025
    "2025-07-01",  # July 1, 2025
    "2025-08-04",  # August 4, 2025
    "2025-09-01",  # September 1, 2025
    "2025-10-13",  # October 13, 2025
    "2025-11-11",  # November 11, 2025
    "2025-12-25",  # December 25, 2025
    "2025-12-26",  # December 26, 2025

]

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, zone: str):
        self._zone = zone.upper()
        if self._zone not in ZONES:
            raise ValueError(f"Invalid zone: {zone}. Must be one of: {', '.join(ZONES.keys())}")
        
        self._zone_config = ZONES[self._zone]

    def _is_holiday(self, date: datetime.date) -> bool:
        """Check if a date is a holiday."""
        date_str = date.strftime("%Y-%m-%d")
        return date_str in HOLIDAY_EXCEPTIONS

    def _adjust_for_holiday(self, date: datetime.date) -> tuple[datetime.date, bool]:
        """
        Adjust collection date if it falls on a holiday.
        Returns tuple of (adjusted_date, was_adjusted)
        """
        if not self._is_holiday(date):
            return date, False

        # Start with next day
        adjusted_date = date + datetime.timedelta(days=1)
        
        # If it falls on a weekend, move to Monday
        while adjusted_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            adjusted_date += datetime.timedelta(days=1)
            
        return adjusted_date, True

    def fetch(self) -> list[Collection]:
        # Get today's date
        today = datetime.date.today()
        
        # Generate next 4 weeks of collection dates
        dates = list(rrule(
            freq=WEEKLY,
            count=4,  # Next 4 collections
            dtstart=today,
            byweekday=self._zone_config["day"]
        ))
        
        # Convert to list of Collections with holiday adjustments
        entries = []
        for date in dates:
            collection_date = date.date()
            adjusted_date, was_adjusted = self._adjust_for_holiday(collection_date)
            
            # Add note if date was adjusted
            if was_adjusted:
                entries.append(
                    Collection(
                        date=adjusted_date,
                        t=f"Garbage & Recycling - {self._zone_config['name']} (Holiday Pickup)"
                    )
                )
            else:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=f"Garbage & Recycling - {self._zone_config['name']}"
                    )
                )
        
        return entries 