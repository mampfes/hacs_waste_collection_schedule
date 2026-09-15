from urllib.parse import quote

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.WhatBinDay import WhatBinDayService

TITLE = "Ipswich City Council"
DESCRIPTION = "Source for Ipswich City Council rubbish collection."
URL = "https://www.ipswich.qld.gov.au"
COUNTRY = "au"
SOURCE_CODEOWNERS = ["@CRZTFR"]
# Every case carries a post_code. Without one the source falls back to the
# council app's shared Google key, which is regularly out of quota, so cases
# omitting it fail on a third party's billing rather than on this source.
TEST_CASES = {
    "Camira State School": {
        "street": "184-202 Old Logan Rd",
        "suburb": "Camira",
        "post_code": "4300",
    },
    "Random": {
        "street": "50 Brisbane Road",
        "suburb": "Redbank",
        "post_code": "4301",
    },
    "Ipswich CBD": {
        "street": "1 Bell Street",
        "suburb": "Ipswich",
        "post_code": "4305",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Use your street number and street name (including the street type, e.g. Road, Street, Avenue) for `street`, and the suburb name only for `suburb`. Do not add QLD or Australia. Adding your `post_code` is optional but recommended: it skips the council app's address search, which is shared between all of its users and is regularly out of quota."
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street number and street name, e.g. 50 Brisbane Road.",
        "suburb": "Suburb name, e.g. Redbank.",
        "post_code": "Optional four-digit post code, e.g. 4301.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street",
        "suburb": "Suburb",
        "post_code": "Post code",
    }
}

APP_PACKAGE = "com.socketsoftware.whatbinday.ipswich"
CONFIG_URL = "https://api.whatbinday.com/V3/Device/{}/Config"

ICON_MAP = {
    "WasteBin": Icons.GENERAL_WASTE,
    "RecycleBin": Icons.RECYCLING,
    "GreenBin": Icons.ORGANIC,
    "GlassBin": Icons.GLASS,
}

BIN_NAMES = {
    "WasteBin": "Waste Bin",
    "RecycleBin": "Recycle Bin",
    "GreenBin": "Garden Organics (GO)",
    "GlassBin": "Glass Bin",
}


class Source:
    def __init__(self, street, suburb, post_code=None):
        self._street = " ".join(str(street).split())
        self._suburb = " ".join(str(suburb).split())
        self._post_code = " ".join(str(post_code or "").split())
        self._service = WhatBinDayService(
            location_key="ipswich_city_council",
            icon_map=ICON_MAP,
            bin_names=BIN_NAMES,
            app_package=APP_PACKAGE,
        )

    def _address_data(self) -> dict:
        """Build the council's address payload without geocoding.

        The service matches on the address components, not the coordinates:
        a payload carrying 0/0 resolves the same schedule as the rooftop
        result Google returns. It does require the Ipswich City council area
        and a post code belonging to the suburb; without either it answers
        "Device Key not valid for location".
        """
        number, _, name = self._street.partition(" ")
        if not name:
            raise SourceArgumentNotFound("street", self._street)
        return {
            "address_components": [
                {"long_name": number, "short_name": number, "types": ["street_number"]},
                {"long_name": name, "short_name": name, "types": ["route"]},
                {
                    "long_name": self._suburb,
                    "short_name": self._suburb,
                    "types": ["locality", "political"],
                },
                {
                    "long_name": "Ipswich City",
                    "short_name": "Ipswich",
                    "types": ["administrative_area_level_2", "political"],
                },
                {
                    "long_name": "Queensland",
                    "short_name": "QLD",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "Australia",
                    "short_name": "AU",
                    "types": ["country", "political"],
                },
                {
                    "long_name": self._post_code,
                    "short_name": self._post_code,
                    "types": ["postal_code"],
                },
            ],
            "formatted_address": (
                f"{self._street}, {self._suburb} QLD {self._post_code}, Australia"
            ),
            "geometry": {"location": {"lat": 0, "lng": 0}},
        }

    def _geocode(self) -> dict:
        device_key = self._service.register_device()
        config_response = requests.get(
            CONFIG_URL.format(device_key),
            headers=self._service.HEADERS,
            timeout=30,
        )
        config_response.raise_for_status()
        config_payload = config_response.json()
        if not config_payload.get("success"):
            raise RuntimeError(
                "Device configuration failed: "
                f"{config_payload.get('info') or 'Unknown error'}"
            )

        search_url = config_payload["data"]["config"]["googleAddressSearchURL"]
        address = f"{self._street}, {self._suburb} QLD, Australia"
        geocode_response = requests.get(
            search_url.replace("%s", quote(address, safe="")),
            headers=self._service.HEADERS,
            timeout=30,
        )
        geocode_response.raise_for_status()
        geocode_payload = geocode_response.json()

        # The key belongs to the council's own app and is shared by every user
        # of it, so it is regularly out of quota. Without this check an
        # exhausted key is indistinguishable from an unknown street, and the
        # visitor is told to correct an address that was right all along.
        status = geocode_payload.get("status")
        if status not in ("OK", "ZERO_RESULTS"):
            raise ValueError(
                "Ipswich City Council's address search is unavailable "
                f"(Google returned {status}). Supplying post_code skips it."
            )

        for result in geocode_payload.get("results", []):
            component_types = {
                component_type
                for component in result.get("address_components", [])
                for component_type in component.get("types", [])
            }
            if {"street_number", "route", "locality"}.issubset(component_types):
                return result

        raise SourceArgumentNotFound("street", self._street)

    def fetch(self) -> list[Collection]:
        location = self._address_data() if self._post_code else self._geocode()
        entries = self._service.get_collection_schedule(location)
        if not entries:
            raise SourceArgumentNotFound("street", self._street)
        return entries
