from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Shire of Murray"
DESCRIPTION = "Source for Shire of Murray waste collection."
URL = "https://www.murray.wa.gov.au/"
COUNTRY = "au"
TEST_CASES = {
    "41 Wilson Road, Pinjarra": {"address": "41 Wilson Road"},
    "58 McLarty Street, Dwellingup": {"address": "58 McLarty Street"},
    "28 Woodview Way, Barragup": {"address": "28 Woodview Way"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Verge Collection - Green waste": "mdi:leaf",
    "Verge Collection - Hard waste": "mdi:dump-truck",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.murray.wa.gov.au/waste-and-environment/waste-and-recycling/bins.aspx and search for your address to verify it is found.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your street address as shown on the Shire of Murray bins page (e.g. '41 Wilson Road').",
    },
}

API_BASE = "https://www.murray.wa.gov.au/api/cms/v1/wastecollection"
ADDRESS_URL = f"{API_BASE}/GetAddressesByQuery"
DETAILS_URL = f"{API_BASE}/GetAddressDetailsByGuid"


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        # Step 1: Look up the address to get a GUID
        r = requests.get(
            ADDRESS_URL, params={"addressQuery": self._address}, timeout=30
        )
        r.raise_for_status()
        addresses = r.json()

        if len(addresses) == 0:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

        if len(addresses) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._address,
                [a["Address"] for a in addresses],
            )

        guid = addresses[0]["Guid"]

        # Step 2: Fetch collection details by GUID
        r = requests.get(DETAILS_URL, params={"id": guid}, timeout=30)
        r.raise_for_status()
        data = r.json()

        entries = []
        for item in data.get("CollectionData", []):
            bin_name = item["BinType"]["Name"]
            date = datetime.strptime(
                item["NextCollectionDate"], "%Y-%m-%dT%H:%M:%S"
            ).date()
            entries.append(
                Collection(
                    date=date,
                    t=bin_name,
                    icon=ICON_MAP.get(bin_name, "mdi:trash-can"),
                )
            )

        return entries
