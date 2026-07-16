import logging

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

from ..service.WhatBinDay import WhatBinDayService

_LOGGER = logging.getLogger(__name__)

TITLE = "City of Kingston"
DESCRIPTION = "Source for City of Kingston (VIC) waste collection."
URL = "https://www.kingston.vic.gov.au"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
TEST_CASES = {
    "randomHouse": {
        "street_number": "30C",
        "street_name": "Oakes Avenue",
        "suburb": "CLAYTON SOUTH",
        "post_code": "3169",
    },
    "randomAppartment": {
        "street_number": "1/51",
        "street_name": "Whatley Street",
        "suburb": "CARRUM",
        "post_code": "3197",
    },
    "randomMultiunit": {
        "street_number": "1/1-5",
        "street_name": "Station Street",
        "suburb": "MOORABBIN",
        "post_code": "3189",
    },
}


ICON_MAP = {
    "WasteBin": Icons.GENERAL_WASTE,
    "RecycleBin": Icons.RECYCLING,
    "GreenBin": Icons.ORGANIC,
}

BIN_NAMES = {
    "WasteBin": "General waste (landfill)",
    "RecycleBin": "Recycling",
    "GreenBin": "Food and garden waste",
}


class Source:
    def __init__(
        self, street_number: str, street_name: str, suburb: str, post_code: str
    ):
        self.street_number = str(street_number)
        self.street_name = str(street_name)
        self.suburb = str(suburb)
        self.post_code = str(post_code)

        self._service: WhatBinDayService | None = None
        self._coordinates: dict | None = None

    def _geocode(self) -> dict:
        """Resolve the address to its real coordinates via Nominatim.

        Kingston's fortnightly recycling / food-and-garden-waste roster
        (and even the weekday of collection) differs from street to
        street, so a single fixed coordinate cannot be used for every
        address: the upstream API resolves the applicable roster from
        the submitted coordinates, not from the address text fields. See
        https://github.com/mampfes/hacs_waste_collection_schedule/issues/6772
        """
        if self._coordinates is not None:
            return self._coordinates

        query = (
            f"{self.street_number} {self.street_name}, "
            f"{self.suburb} VIC {self.post_code}, Australia"
        )
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": "1",
                "countrycodes": "au",
            },
            headers={"User-Agent": "hacs_waste_collection_schedule"},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise SourceArgumentNotFound("street_name", self.street_name)

        self._coordinates = {
            "lat": float(results[0]["lat"]),
            "lng": float(results[0]["lon"]),
        }
        return self._coordinates

    def _get_service(self) -> WhatBinDayService:
        """Get or create the WhatBinDay service instance."""
        if self._service is None:
            # Create location key for this address
            location_key = f"{self.street_number}_{self.street_name}_{self.suburb}_{self.post_code}"

            # Create service with custom mappings for Kingston
            self._service = WhatBinDayService(
                location_key=location_key,
                icon_map=ICON_MAP,
                bin_names=BIN_NAMES,
                app_package="com.socketsoftware.whatbinday.binston",
            )

        return self._service

    def fetch(self) -> list[Collection]:
        """Fetch waste collection schedule."""
        service = self._get_service()
        coordinates = self._geocode()
        return service.fetch_collections(
            self.street_number,
            self.street_name,
            self.suburb,
            self.post_code,
            state="VIC",
            country="Australia",
            coordinates=coordinates,
        )
