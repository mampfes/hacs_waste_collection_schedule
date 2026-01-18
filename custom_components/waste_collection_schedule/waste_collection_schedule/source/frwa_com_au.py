import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = (
    "Fleurieu Regional Waste Authority"  # Title will show up in README.md and info.md
)
DESCRIPTION = (
    "Source script for fleurieuregionalwasteauthority.com.au"  # Describe your source
)
URL = "https://fleurieuregionalwasteauthority.com.au"  # Insert url to service homepage. URL will show up in README.md and info.md

TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Test_001": {
        "name_or_number": "42",
        "address": "WISHART CRESCENT",
        "district": "ENCOUNTER BAY",
    },
    "Test_002": {
        "name_or_number": "15",
        "address": "Bell Court",
        "district": "ENCOUNTER BAY",
    },
    "Test_003": {
        "name_or_number": "15",
        "address": "Bell Court",
        "district": "Kingscote",
    },
}

API_URLS = {
    "HOME": "https://fleurieuregionalwasteauthority.com.au/collection-calendar-downloads",
    "SEARCH": "https://fleurieuregionalwasteauthority.com.au/wp-admin/admin-ajax.php",
}
ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}
HEADERS = {"user-agent": "Mozilla/5.0"}


class Source:
    def __init__(
        self, name_or_number=int | str, address=str, district=str
    ):  # argX correspond to the args dict in the source configuration
        self._name_or_number = str(name_or_number).upper()
        self._address = address.upper()
        self._district = district.upper()
        self._id: str = None

    def fetch(self):

        s = requests.Session()

        # get security token
        r = s.get(API_URLS["HOME"], headers=HEADERS)
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        script_text = soup.find("script", {"id": "autocomplete-search-js-extra"}).string
        json_text = script_text.split("=", 1)[1].rsplit(";", 1)[0].strip()
        data = json.loads(json_text)
        token = data["ajax_nonce"]

        # get unique ID from address search
        params = {
            "term": f"{self._name_or_number} {self._address}",
            "action": "autocomplete_search",
            "security": token,
        }
        address_json = s.get(API_URLS["SEARCH"], params=params, headers=HEADERS).json()
        for item in address_json:
            if (
                self._name_or_number in item["label"]
                and self._address in item["label"]
                and self._district in item["label"]
            ):
                self._id = item["id"]
        if self._id is None:
            raise Exception(
                f"Unable to find an address match for {self._name_or_number} {self._address} in {self._district}"
            )

        # retrieve schedule
        params = {
            "id": self._id,
            "action": "fetch_bin_collection",
        }
        r = s.post(API_URLS["SEARCH"], params=params, headers=HEADERS)
        soup = BeautifulSoup(r.content, "html.parser")

        # extract collections
        entries = []
        for block in soup.select("div.coll-main-wrap"):
            waste_type = block.find("h6").get_text(strip=True).split(" Collection")[0]
            next_date = None
            for row in block.select("table tr"):
                label = row.find_all("td")[0].get_text(strip=True)
                if label == "Next Collection Date:":
                    next_date = row.find_all("td")[1].get_text(strip=True)
            entries.append(
                Collection(
                    date=datetime.strptime(next_date, "%d %B %Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
