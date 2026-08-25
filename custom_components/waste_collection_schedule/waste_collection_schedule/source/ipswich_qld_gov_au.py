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
TEST_CASES = {
    "Camira State School": {"street": "184-202 Old Logan Rd", "suburb": "Camira"},
    "Random": {"street": "50 Brisbane Road", "suburb": "Redbank"},
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
    def __init__(self, street, suburb):
        self._street = " ".join(str(street).split())
        self._suburb = " ".join(str(suburb).split())
        self._service = WhatBinDayService(
            location_key="ipswich_city_council",
            icon_map=ICON_MAP,
            bin_names=BIN_NAMES,
            app_package=APP_PACKAGE,
        )

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
                f"Device configuration failed: {config_payload.get('info', '')}"
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
        entries = self._service.get_collection_schedule(self._geocode())
        if not entries:
            raise SourceArgumentNotFound("street", self._street)
        return entries
