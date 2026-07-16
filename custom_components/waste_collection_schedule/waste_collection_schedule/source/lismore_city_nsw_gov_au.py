import re

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.WhatBinDay import WhatBinDayService

TITLE = "Lismore City Council"
DESCRIPTION = (
    "Source for Lismore City Council waste collection services in NSW, Australia."
)
URL = "https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1"
COUNTRY = "au"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the full service address used by Lismore City Council, for example "
        "'1 Rosella Chase, Goonellabah NSW 2480'."
    )
}
PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full service address (e.g. '1 Rosella Chase, Goonellabah NSW 2480')"
    }
}
PARAM_TRANSLATIONS = {"en": {"address": "Address"}}
TEST_CASES = {
    "1 Rosella Chase, Goonellabah NSW 2480": {
        "address": "1 Rosella Chase, Goonellabah NSW 2480"
    },
    "10 Sibley St, NIMBIN NSW 2480": {"address": "10 Sibley St, NIMBIN NSW 2480"},
}

ICON_MAP = {
    "WasteBin": Icons.GENERAL_WASTE,
    "RecycleBin": Icons.RECYCLING,
    "GreenBin": Icons.ORGANIC,
}

BIN_NAMES = {
    "WasteBin": "General Waste",
    "RecycleBin": "Recycling",
    "GreenBin": "Green Waste",
}


class Source:
    def __init__(self, address: str):
        self._address = " ".join(address.split())
        self._service = WhatBinDayService(
            location_key="lismore_city_council",
            icon_map=ICON_MAP,
            bin_names=BIN_NAMES,
        )

    def fetch(self) -> list[Collection]:
        parsed_address = self._split_address(self._address)
        try:
            entries = self._service.fetch_collections(
                street_number=parsed_address["street_number"],
                street_name=parsed_address["route"],
                suburb=parsed_address["locality"],
                post_code=parsed_address["postal_code"],
                state=parsed_address["state"],
            )
        except Exception as e:
            raise SourceArgumentNotFound("address", self._address) from e

        if not entries:
            raise SourceArgumentNotFound("address", self._address)
        return entries

    def _split_address(self, address: str) -> dict[str, str]:
        normalized = " ".join(address.replace(",", " , ").split())
        match = re.match(
            r"^(?:(?P<subpremise>(?:[A-Za-z]+\s+)?\d+[A-Za-z]?)\/)?"
            r"(?P<street_number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+"
            r"(?P<route>.+?)\s*,?\s+"
            r"(?P<locality>[A-Za-z ]+?)\s+"
            r"(?P<state>NSW|VIC|QLD|SA|WA|TAS|ACT|NT)\s+"
            r"(?P<postal_code>\d{4})$",
            normalized,
            flags=re.IGNORECASE,
        )
        if not match:
            raise SourceArgumentNotFound("address", address)

        subpremise = (match.group("subpremise") or "").strip()
        street_number = match.group("street_number").strip()
        route = match.group("route").replace(" , ", " ").strip()
        locality = match.group("locality").strip().upper()
        state = match.group("state").strip().upper()
        postal_code = match.group("postal_code").strip()
        address_prefix = (
            f"{subpremise}/{street_number}" if subpremise else street_number
        )
        formatted_address = (
            f"{address_prefix} {route}, {locality} {state} {postal_code}"
        )

        return {
            "subpremise": subpremise,
            "street_number": street_number,
            "route": route,
            "locality": locality,
            "state": state,
            "postal_code": postal_code,
            "formatted_address": formatted_address,
        }
