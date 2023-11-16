from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wokingham Borough Council"
DESCRIPTION = "Source for wokingham.gov.uk services for Wokingham, UK."
URL = "https://wokingham.gov.uk"
API_URL = (
    "https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day"
)
TEST_CASES = {
    "Test_001": {"postcode": "RG40 1GE", "property": "56199"},
    "Test_002": {"postcode": "RG413BP", "property": "55588"},
    "Test_003": {"postcode": "rg41 1ph", "property": 61541},
    "Test_004": {"postcode": "RG40 2LW", "address": "16 Davy Close"},
}
ICON_MAP = {
    "HOUSEHOLD WASTE AND RECYCLING": "mdi:trash-can",
    "GARDEN WASTE": "mdi:leaf",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.wokingham.gov.uk",
    "Origin": "https://www.wokingham.gov.uk",
    "Referer": "https://www.wokingham.gov.uk/rubbish-and-recycling/find-your-bin-collection-day",
}


class Source:
    def __init__(self, postcode=None, property=None, address=None):
        self._postcode = postcode
        self._property = property
        self._address = address

    def get_form_id(self, txt: str) -> str:
        soup = BeautifulSoup(txt, "html.parser")
        x = soup.find("input", {"name": "form_build_id"})
        id = x.get("value")
        return id

    def match_address(self, lst: list, addr: str) -> str:
        for item in lst:
            if addr in item.text.replace(",", ""):
                a = item.get("value")
        return a

    def fetch(self):

        s = requests.Session()

        # Load page to generate token needed for subsequent query
        r = s.get(
            API_URL,
        )
        form_id = self.get_form_id(r.text)

        # Perform postcode search to generate token needed for following query
        self._postcode = str(self._postcode.upper().strip().replace(" ", ""))
        payload = {
            "postcode_search": self._postcode,
            "op": "Find address",
            "form_build_id": form_id,
            "form_id": "waste_collection_information",
        }
        r = s.post(
            API_URL,
            headers=HEADERS,
            data=payload,
        )
        form_id = self.get_form_id(r.text)

        # Use address to get an ID if property wasn't supplied. Assumes first match is correct.
        if self._property is None:
            soup = BeautifulSoup(r.text, "html.parser")
            dropdown = soup.find("div", {"class": "form-item__dropdown"})
            addresses = dropdown.find_all("option")
            self._address = self._address.upper()
            self._property = self.match_address(addresses, self._address)
        else:
            self._property = str(self._property)

        # Now get the collection schedule
        payload = {
            "postcode_search": self._postcode,
            "address_options": self._property,
            "op": "Show collection dates",
            "form_build_id": form_id,
            "form_id": "waste_collection_information",
        }
        r = s.post(
            API_URL,
            headers=HEADERS,
            data=payload,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table", {"class": "table--non-responsive"})

        # Extract the collection schedules
        entries = []
        for table in tables:
            waste_type = table.find("th").text
            waste_date = table.find_all("td")[-1].text
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%d/%m/%Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
