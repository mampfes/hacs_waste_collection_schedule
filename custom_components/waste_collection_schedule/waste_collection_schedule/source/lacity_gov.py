from datetime import date, timedelta

import requests
from requests import RequestException
from waste_collection_schedule import Collection
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
    "BLACK BIN": "mdi:trash-can",  # Regular trash
    "BLUE BIN": "mdi:recycle",  # Recycling
    "GREEN BIN": "mdi:leaf",  # Organics
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
            raise Exception(f"Error fetching collection data: {str(ex)}")

        # Verify Address was found
        if data["status"] != "exactMatch":
            raise SourceArgumentException(
                argument=self._street_address,
                message=data["message"],
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

        # Get Next 2 Weeks for Collection Dates
        today = date.today()
        for i in range(14):  # Look ahead 2 weeks
            check_date = today + timedelta(days=i)
            if check_date.weekday() == collection_weekday:
                for waste_type in ICON_MAP:
                    entries.append(
                        Collection(
                            date=check_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
        return entries
