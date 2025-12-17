import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
)

TITLE = "Greater Cambridge Waste, UK"
DESCRIPTION = "Source for greatercambridgewaste.org, the shared recycling and waste service for Cambridge City Council and South Cambridgeshire District Council, UK"
URL = "greatercambridgewaste.org"
TEST_CASES = {
    "Cambs_uprn": {"uprn": 200004170895},
    "Cambs_houseNumber": {"postcode": "CB13JD", "name_or_number": 37},
    "Cambs_houseName": {"postcode": "cb215hd", "name_or_number": "ROSEMARY HOUSE"},
    "SCambs_uprn": {"uprn": 10091624540},
    "SCambs_houseNumber": {"postcode": "CB236GZ", "name_or_number": 53},
    "SCambs_houseName": {
        "postcode": "CB225HT",
        "name_or_number": "Rectory Farm Cottage",
    },
}
API_URLS = {
    "uprn": "https://www.greatercambridgewaste.org/bin-calendar/collections",
    "postcode": "https://www.greatercambridgewaste.org/bin-calendar/addresses",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "BLACK BIN": "mdi:trash-can",
    "BLUE BIN": "mdi:recycle",
    "GREEN BIN": "mdi:leaf",
    "FOOD CADDY": "mdi:food",
}
REGEX = {
    "details": (
        r'data-address\s*=\s*"([^"]+)"'  # group 1 = address
        r"\s*.*?"  # any characters
        r'data-id\s*=\s*"([^"]+)"'  # group 2 = uprn
    ),
    "schedule": r'aria-label="([^"]+)"',
}


class Source:
    def __init__(
        self,
        uprn: str | int | None = None,
        postcode: str | None = None,
        name_or_number: str | int | None = None,
    ) -> None:

        if uprn is not None:
            self._uprn = str(uprn)
            self._postcode = None
            self._number = None
        else:
            self._uprn = ""
            self._postcode = str(postcode).strip().replace(" ", "").upper()
            self._name_or_number = str(name_or_number).upper()

    def get_address_details(self, a: str) -> str:
        matches = re.findall(REGEX["details"], a, flags=re.IGNORECASE | re.DOTALL)
        temp_id: list = [
            did.strip() for addr, did in matches if self._name_or_number in addr
        ][0]
        return str(temp_id)

    def fetch(self) -> Collection:
        s = requests.Session()

        if self._postcode:
            # use address detail to get uprn
            params = {"postcode": self._postcode}
            r = s.get(API_URLS["postcode"], params=params, headers=HEADERS)
            if r.status_code == 400:
                raise SourceArgumentNotFound("post_code", self._postcode)
            r.raise_for_status()
            addresses = r.json()
            self._uprn = self.get_address_details(addresses["addresses"].upper())

        # get collection schedule using uprn
        params = {"uprn": self._uprn, "numberOfCollections": "12"}
        r = s.get(API_URLS["uprn"], params=params, headers=HEADERS)
        r.raise_for_status()

        r_json = r.json()["tableRows"]
        collections = re.findall(REGEX["schedule"], r_json, flags=re.IGNORECASE)

        entries = []
        for item in collections:
            waste, dt = item.split(" collection on ")
            entries.append(
                Collection(
                    date=datetime.strptime(dt, "%A %d %B %Y").date(),
                    t=waste,
                    icon=ICON_MAP.get(waste.upper()),
                )
            )

        return entries
