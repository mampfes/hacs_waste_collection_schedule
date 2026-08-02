import logging

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

from ..service.WhatBinDay import WhatBinDayService

_LOGGER = logging.getLogger(__name__)

TITLE = "Surf Coast Shire"
DESCRIPTION = "Source for Surf Coast Shire (VIC) waste collection."
URL = "https://www.surfcoast.vic.gov.au"
COUNTRY = "au"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit the Surf Coast Shire 'Bin collection calendars' page "
        "(https://www.surfcoast.vic.gov.au/Property/Waste-and-recycling/Kerbside-bins/Bin-collection-calendars), "
        "search for your address, and enter the street number, street name, "
        "suburb and postcode exactly as they appear (suburb must be in "
        "Title Case, e.g. 'Torquay', not 'TORQUAY')."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_number": "Street number (e.g. '20')",
        "street_name": "Street name (e.g. 'Bell Street')",
        "suburb": "Suburb, in Title Case (e.g. 'Torquay')",
        "post_code": "Postcode (e.g. '3228')",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_number": "Street number",
        "street_name": "Street name",
        "suburb": "Suburb",
        "post_code": "Post code",
    }
}

TEST_CASES = {
    "Bell Street Torquay": {
        "street_number": "20",
        "street_name": "Bell Street",
        "suburb": "Torquay",
        "post_code": "3228",
    },
    "Mountjoy Parade Lorne": {
        "street_number": "1",
        "street_name": "Mountjoy Parade",
        "suburb": "Lorne",
        "post_code": "3232",
    },
    "Noble Street Anglesea": {
        "street_number": "1",
        "street_name": "Noble Street",
        "suburb": "Anglesea",
        "post_code": "3230",
    },
}


ICON_MAP = {
    "WasteBin": Icons.GENERAL_WASTE,
    "RecycleBin": Icons.RECYCLING,
    "GreenBin": Icons.ORGANIC,
    "GlassBin": Icons.GLASS,
}

BIN_NAMES = {
    "WasteBin": "General waste (landfill)",
    "RecycleBin": "Recycling",
    "GreenBin": "Food and garden waste",
    "GlassBin": "Glass",
}


class Source:
    def __init__(
        self, street_number: str, street_name: str, suburb: str, post_code: str
    ):
        self.street_number = str(street_number)
        self.street_name = str(street_name)
        # Surf Coast Shire's WhatBinDay backend matches the suburb name
        # case-sensitively against its own dataset (e.g. "Torquay", not
        # "TORQUAY"), so normalise user input to Title Case.
        self.suburb = str(suburb).strip().title()
        self.post_code = str(post_code)

        self._service = WhatBinDayService(
            location_key=(
                f"{self.street_number}_{self.street_name}_"
                f"{self.suburb}_{self.post_code}"
            ),
            icon_map=ICON_MAP,
            bin_names=BIN_NAMES,
            app_package="com.socketsoftware.whatbinday.surfcoast",
        )

    def _geocode(self) -> dict:
        """Resolve the address to coordinates via Nominatim.

        Surf Coast Shire's roster lookup requires coordinates close to the
        actual property (unlike some other WhatBinDay-backed councils, a
        generic/default coordinate does not resolve to any bin service),
        so we geocode the full address first.
        """
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

        return {
            "lat": float(results[0]["lat"]),
            "lng": float(results[0]["lon"]),
        }

    def _build_location_data(self, coordinates: dict) -> dict:
        """Build the WhatBinDay address payload.

        The shared WhatBinDayService.build_address_data() helper uses the
        same string for both the state's long_name and short_name. Surf
        Coast Shire's backend requires the full state name ("Victoria") as
        the long_name, so the payload is built manually here instead of
        via that helper.
        """
        formatted_address = (
            f"{self.street_number} {self.street_name}, "
            f"{self.suburb} VIC {self.post_code}, Australia"
        )
        return {
            "address_components": [
                {
                    "long_name": self.street_number,
                    "short_name": self.street_number,
                    "types": ["street_number"],
                },
                {
                    "long_name": self.street_name,
                    "short_name": self.street_name,
                    "types": ["route"],
                },
                {
                    "long_name": self.suburb,
                    "short_name": self.suburb,
                    "types": ["locality", "political"],
                },
                {
                    "long_name": self.post_code,
                    "short_name": self.post_code,
                    "types": ["postal_code"],
                },
                {
                    "long_name": "Victoria",
                    "short_name": "VIC",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "Australia",
                    "short_name": "AU",
                    "types": ["country", "political"],
                },
            ],
            "formatted_address": formatted_address,
            "geometry": {
                "location": coordinates,
                "location_type": "APPROXIMATE",
            },
        }

    def fetch(self) -> list[Collection]:
        coordinates = self._geocode()
        location_data = self._build_location_data(coordinates)

        entries = self._service.get_collection_schedule(location_data)
        if not entries:
            raise SourceArgumentNotFound("street_name", self.street_name)
        return entries
