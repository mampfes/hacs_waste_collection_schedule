import datetime
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Greater Cambridge Waste, UK"
DESCRIPTION = "Source for greatercambridgewaste.org, the shared recycling and waste service for Cambridge City Council and South Cambridgeshire District Council, UK"
URL = "greatercambridgewaste.org"
TEST_CASES = {
    "Cambs_uprn": {"uprn": 000},
    "Cambs_houseNumber": {"postcode": "CB13JD", "name_or_": 37},
    "Cambs_houseName": {"postcode": "cb215hd", "name_or_": "ROSEMARY HOUSE"},
    "SCambs_uprn": {"uprn": 000},
    "SCambs_houseNumber": {"postcode": "CB236GZ", "name_or_number": 53},
    "SCambs_houseName": {"postcode": "CB225HT", "name_or_": "Rectory Farm Cottage"},
}
API_URLS = {
    "uprn": "https://www.greatercambridgewaste.org/bin-calendar/collections",
    "postcode": "https://www.greatercambridgewaste.org/bin-calendar/addresses",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Black Bin": "mdi:trash-can",
    "Blue Bin": "mdi:recycle",
    "Green Bin": "mdi:leaf",
    "Food Caddy": "mdi:food",
}

# _LOGGER = logging.getLogger(__name__)


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
            self._postcode = str(postcode).strip().replace(" ", "")
            self._name_or_number = str(name_or_number).capitalize()

    def fetch(self):
        s = requests.Session()

        if self._postcode:
            # use address detail to get uprn
            params = {"postcode": self._postcode}
            r = s.get(API_URLS["postcode"], params=params, headers=HEADERS)
            if r.status_code == 400:
                raise SourceArgumentNotFound("post_code", self._post_code)
            r.raise_for_status()

            addresses = r.json()
            address_ids = [
                x["data-id"]
                for x in addresses
                if x["data-address"].capitalize() == self._name_or_number
            ]
            if len(address_ids) == 0:
                raise SourceArgumentNotFoundWithSuggestions(
                    "number",
                    self._name_or_number,
                    [x["data-address"] for x in addresses],
                )
            else:
                self._uprn = address_ids[0]

        # get collection schedule using uprn
        params = {"uprn": self._uprn, "numberOfCollections": 12}
        r = s.get(API_URLS["uprn"], params=params, headers=HEADERS)
        r.raise_for_status()

        r_json = r.json()["tableRows"]
        pattern = r'aria-label="([^"]+)"'
        collections = re.findall(pattern, r_json, flags=re.IGNORECASE)

        entries = []
        for item in collections:
            waste, dt = item.split(" collection on ")
            entries.append(
                Collection(
                    date=datetime.strptime(dt, "%A %d %B %Y").date(),
                    t=waste.capitalize(),
                    icon=ICON_MAP.get(waste.capitalize()),
                )
            )

        return entries
