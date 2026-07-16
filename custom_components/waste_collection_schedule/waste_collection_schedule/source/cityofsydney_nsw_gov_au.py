from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Sydney"
DESCRIPTION = "Source for City of Sydney (NSW) bin collection."
URL = "https://www.cityofsydney.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {
    "17 Junction Street, Forest Lodge": {
        "address": "17 Junction Street, Forest Lodge",
    },
    "216 Chalmers Street, Redfern": {
        "address": "216 Chalmers Street, Redfern",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '17 Junction Street, Forest Lodge'), as it would appear on "
    "https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '17 Junction Street, Forest Lodge')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

SOURCE_CODEOWNERS: list[str] = []

# The council's official bin-collection lookup page
# (https://www.cityofsydney.nsw.gov.au/waste-recycling-services/find-my-bin-collection-day)
# embeds a widget hosted on this domain, which in turn proxies the council's
# own "lga/property" API. This is the same endpoint the official page uses.
API_BASE = "https://cos-bin-collection-widget.netlify.app/api"
SEARCH_URL = f"{API_BASE}/search"
COLLECTION_URL = f"{API_BASE}/property/{{property_key}}/bins-collection"

HEADERS = {
    "Accept": "application/json",
}

# Matches the friendly-name mapping used by the official widget.
TYPE_MAP = {
    "Waste": "Rubbish",
    "Green Waste": "Garden organics",
    "Food Scraps": "Food scraps",
}

ICON_MAP = {
    "WAS": Icons.GENERAL_WASTE,
    "RCY": Icons.RECYCLING,
    "GRE": Icons.GARDEN,
    "FOO": Icons.BIO_KITCHEN,
}

DATE_FORMAT = "%A %d/%m/%Y"


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def _search_properties(self) -> list[dict]:
        r = requests.get(SEARCH_URL, params={"address": self._address}, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        return data.get("matchingProperties") or []

    def _resolve_property_key(self) -> int:
        matches = self._search_properties()

        if not matches:
            raise SourceArgumentNotFound("address", self._address)

        if len(matches) == 1:
            return int(matches[0]["propertyKey"])

        normalized = self._address.strip().lower()
        for match in matches:
            if match["fullAddress"].strip().lower() == normalized:
                return int(match["propertyKey"])

        raise SourceArgumentNotFoundWithSuggestions(
            "address",
            self._address,
            [match["fullAddress"] for match in matches],
        )

    def fetch(self) -> list[Collection]:
        property_key = self._resolve_property_key()

        r = requests.get(
            COLLECTION_URL.format(property_key=property_key), headers=HEADERS
        )
        if r.status_code == 204:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "no bin collection schedule is available for this property "
                "(it may not be a standard residential property in the "
                "City of Sydney area, e.g. a multi-unit building serviced "
                "separately).",
            )
        r.raise_for_status()
        data = r.json()

        entries: list[Collection] = []
        for bin_info in data.get("bins", []):
            round_code = bin_info.get("roundCode")
            round_description = bin_info.get("roundDescription", "")
            waste_type = TYPE_MAP.get(round_description, round_description)
            icon = ICON_MAP.get(round_code)

            for date_key in ("nextPickupDate", "pickupDateAfterNext"):
                date_str = bin_info.get(date_key)
                if not date_str:
                    continue
                try:
                    date = datetime.strptime(date_str, DATE_FORMAT).date()
                except ValueError:
                    continue
                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
