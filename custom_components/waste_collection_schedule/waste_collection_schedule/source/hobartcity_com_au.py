from datetime import datetime
from typing import TypedDict

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "City of Hobart "
DESCRIPTION = "Source for City of Hobart"
URL = "https://www.hobartcity.com.au"
TEST_CASES = {
    "154  FOREST ROAD, WEST HOBART Tasmania 7000": {
        "address": "154  FOREST ROAD, WEST HOBART Tasmania 7000"
    },
    "151  AUGUSTA ROAD, LENAH VALLEY Tasmania 7008": {
        "address": "151  AUGUSTA ROAD, LENAH VALLEY Tasmania 7008"
    },
}


ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "fogo": "mdi:leaf",
}

SEARCH_URL = "https://www.hobartcity.com.au/api/v1/myarea/search"
API_URL = "https://www.hobartcity.com.au/ocapi/Public/myarea/wasteservices"
API_PARAMS = {
    "geolocationid": "",  # filled in later
    "ocsvclang": "en-AU",
    "pageLink": "/$720cfbd8-df7e-4b88-bf92-e218d51ee173$/Residents/Waste-and-recycling/When-is-my-bin-collected",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "The address should exactly match the address autocompleted by the website: https://www.hobartcity.com.au/Residents/Waste-and-recycling/When-is-my-bin-collected",
    }
}


class Address(TypedDict):
    Id: str
    AddressSingleLine: str
    MunicipalSubdivision: str
    Distance: int
    Score: float
    LatLon: None


class Source:
    def __init__(self, address: str) -> None:
        self._address: str = address
        self._address_id: str | None = None

    def _fetch_address_id(self) -> None:
        args = {"keywords": self._address}
        r = requests.get(SEARCH_URL, params=args)
        r.raise_for_status()
        addresses: list[Address] = r.json()["Items"]
        if len(addresses) == 1:
            self._address_id = addresses[0]["Id"]
            return

        for address in addresses:
            if address["AddressSingleLine"].lower().replace(
                " ", ""
            ) == self._address.lower().replace(" ", ""):
                self._address_id = address["Id"]
                return
        raise SourceArgumentNotFoundWithSuggestions(
            argument="address",
            value=self._address,
            suggestions=[a["AddressSingleLine"] for a in addresses],
        )

    def fetch(self) -> list[Collection]:
        fresh = False
        if not self._address_id:
            self._fetch_address_id()
            fresh = True
        try:
            return self.get_collections()
        except Exception as e:
            if fresh:
                raise e
            return self.get_collections()

    def get_collections(self) -> list[Collection]:
        if not self._address_id:
            raise ValueError("Address ID not set")  # this should never happen
        params = API_PARAMS.copy()
        params["geolocationid"] = self._address_id
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if data["success"] is False:
            raise ValueError("API request failed")

        soup = BeautifulSoup(data["responseContent"], "html.parser")
        entries = []
        for article in soup.select("article"):
            bin_type = article.select_one("h3").text.strip()
            date_tag = article.select_one("div.next-service").text.strip()
            # Wed 4/12/2024
            date_ = datetime.strptime(date_tag, "%a %d/%m/%Y").date()
            icon = ICON_MAP.get(bin_type.lower().split("/")[0])
            entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
