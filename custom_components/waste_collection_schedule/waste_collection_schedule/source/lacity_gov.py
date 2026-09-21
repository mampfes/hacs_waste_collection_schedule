from datetime import date, timedelta

import requests
from requests import RequestException
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentRequired,
)

TITLE = "City of Los Angeles, CA"
DESCRIPTION = "Source script for Los Angeles, California waste collection services"
URL = "https://www.lacitysan.org"
COUNTRY = "us"
TEST_CASES = {
    "East Valley District Yard": {"street_address": "11050 Pendleton Street"},
    "West Valley District Yard": {"street_address": "8840 Vanalden Avenue"},
    "North Central District Yard": {"street_address": "452 North San Fernando Road"},
    "South Los Angeles District Yard": {"street_address": "786 South Mission Road"},
    "Harbor District Yard": {"street_address": "1400 North Gaffey Street"},
    "West Los Angeles District Yard": {"street_address": "2027 Stoner Avenue"},
}

ICON_MAP = {
    "BLACK BIN": Icons.GENERAL_WASTE,
    "BLUE BIN": Icons.RECYCLING,
    "GREEN BIN": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your street address exactly as it appears on your LA Sanitation bill. "
        "The address must be within Los Angeles city limits."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_address": "Your complete street address without city/state (e.g. '22472 Denker Ave')"
    }
}


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _delay_holidays(year: int) -> list[date]:
    """Holidays after which LA Sanitation delays collection by one day.

    See https://sanitation.lacity.gov/services/lasan-holiday-collection-delays
    Holidays on a weekend cause no delay, so they are ignored by the caller.
    """
    return [
        date(year, 1, 1),  # New Year's Day
        date(year, 7, 4),  # Independence Day
        _nth_weekday(year, 9, 0, 1),  # Labor Day (first Monday of September)
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving (fourth Thursday of November)
        date(year, 12, 25),  # Christmas Day
    ]


def _apply_holiday_delay(collection_date: date) -> date:
    """Shift a regular collection date by one day if a weekday holiday
    occurred earlier in the same week (or on the collection day itself)."""
    week_start = collection_date - timedelta(days=collection_date.weekday())
    for holiday in _delay_holidays(collection_date.year):
        if holiday.weekday() < 5 and week_start <= holiday <= collection_date:
            return collection_date + timedelta(days=1)
    return collection_date


class Source:
    def __init__(self, street_address: str):
        """Initialize the LA City waste collection source.

        Args:
            street_address: Street address in Los Angeles

        Raises:
            SourceArgumentRequired: If street_address is not provided
        """
        if not street_address:
            raise SourceArgumentRequired(
                "street_address",
                "A valid street address in Los Angeles is required to look up collection schedule",
            )

        self._street_address = street_address
        self._api_key = (
            "YsvfDePjTDKtLl041Vz25jCbfjExMtCh"  # Public API key from LA City website
        )
        self._api_url = "https://api.lacity.org/boe_geoquery/addressvalidationservice"

    def fetch(self) -> list[Collection]:
        params = {
            "address": self._street_address,
            "status": "new",
            "layerset": "neighborhoodinfo",
            "apikey": self._api_key,
        }

        try:
            response = requests.get(self._api_url, params=params)
            response.raise_for_status()
            data = response.json()

        except RequestException as ex:
            raise Exception(f"Error fetching collection data: {ex!s}") from ex

        # Verify Address was found
        if data["status"] != "exactMatch":
            raise SourceArgumentException(
                argument=self._street_address,
                message=data.get("message", "Address not found"),
            )

        # Get Collection Day
        weekday_map = {
            "MONDAY": 0,
            "TUESDAY": 1,
            "WEDNESDAY": 2,
            "THURSDAY": 3,
            "FRIDAY": 4,
        }
        collection_day = data["layers"]["merge"]["day"]
        collection_weekday = weekday_map[collection_day]

        entries = []

        # Get Next 2 Weeks for Collection Dates. Start one day back so that a
        # pickup delayed by a holiday and landing on today is still included.
        today = date.today()
        for i in range(-1, 14):
            check_date = today + timedelta(days=i)
            if check_date.weekday() == collection_weekday:
                actual_date = _apply_holiday_delay(check_date)
                if actual_date < today:
                    continue
                for waste_type in ICON_MAP:
                    entries.append(
                        Collection(
                            date=actual_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
        return entries
