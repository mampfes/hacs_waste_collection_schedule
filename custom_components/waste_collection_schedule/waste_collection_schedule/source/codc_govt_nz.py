from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Central Otago District Council"
DESCRIPTION = (
    "Source for Central Otago District Council Rubbish & Recycling collection."
)
URL = "https://www.codc.govt.nz/"
TEST_CASES = {
    "Alexandra": {"address": "5 Campbell Street Alexandra"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "RED BIN": Icons.GENERAL_WASTE,
    "BLUE BIN": Icons.GLASS,
    "YELLOW BIN": Icons.PLASTIC_PACKAGING,
    "GREEN BIN": Icons.ORGANIC,
}

# CODC's API returns "ORG" for organics rather than "FOD" (used by some other
# councils on the same Environz backend), so both are mapped for safety.
OLD_BIN_MAP = {
    "REC": "YELLOW BIN",
    "GLA": "BLUE BIN",
    "REF": "RED BIN",
    "ORG": "GREEN BIN",
    "FOD": "GREEN BIN",
}

API_URL = "https://environz-api.azurewebsites.net/api/codc/nextservicedate"
API_KEY = "bPLjJjgubEyQ3ruJqjhFenL1SoHCTzNEVGoLY5MJpP9AAzFuj8pSzA=="

SOURCE_CODEOWNERS = ["@soasmileynz"]


class Source:
    def __init__(self, address):
        self._address = str(address).strip()
        split = self._address.split("-")
        if len(split) > 1 and split[0].strip().isdigit():
            split = [split[0].strip() + "/" + split[1].strip(), *split[2:]]
            self._address = "-".join(split)

    def fetch(self):
        end_date = (datetime.now() + timedelta(days=365)).strftime("%d/%m/%Y")
        params = {
            "code": API_KEY,
            "address": self._address,
            "endDate": end_date,
            "postcode": "",
        }

        r = requests.get(API_URL, params=params, headers=HEADERS)
        if r.status_code == 400:
            raise SourceArgumentNotFound(
                argument="address",
                value=self._address,
                message_addition="make sure the address matches an address that has a schedule in the CODC Bin App.",
            )

        r.raise_for_status()

        data = r.json()

        entries = []
        for key, value in data.items():
            if not key.startswith("route") or not value:
                continue
            collection_type = key.removeprefix("route").strip()
            collection_type = OLD_BIN_MAP.get(collection_type, collection_type)
            for date in value.values():
                entries.append(
                    Collection(
                        date=datetime.strptime(date, "%d/%m/%Y").date(),
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type.upper()),
                    )
                )
        return entries
