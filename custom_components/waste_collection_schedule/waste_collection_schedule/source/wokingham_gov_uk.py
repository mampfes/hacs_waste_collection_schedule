from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wokingham Borough Council"
DESCRIPTION = "Source for wokingham.gov.uk services for Wokingham, UK."
URL = "https://wokingham.gov.uk"
API_URL = (
    "https://www.wokingham.gov.uk/rubbish-and-recycling/find-your-bin-collection-day"
)
TEST_CASES = {
    "Test_001": {"postcode": "GR40 1GE", "property": "56199"},
    "Test_002": {"postcode": "WN6 8RG", "property": "55602"},
    "Test_003": {"postcode": "wn36au", "property": 61541},
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
    def __init__(self, postcode, property):
        self._postcode = str(postcode.upper().strip().replace(" ", ""))
        self._property = str(property)

    def get_form_id(self, txt: str) -> str:
        soup = BeautifulSoup(txt, "html.parser")
        x = soup.find("input", {"name": "form_build_id"})
        id = x.get("value")
        return id

    def fetch(self):

        s = requests.Session()

        # load page to generate token needed for subsequent query
        r = s.get(
            API_URL,
        )
        form_id = self.get_form_id(r.text)
        # soup = BeautifulSoup(r.text, "html.parser")
        # x = soup.find("input", {"name": "form_build_id"})
        # form_id = x.get("value")

        # Perform postcode search to generate token needed for following query
        payload = {
            "postcode_search": self._postcode,
            "op": "Find+Address",
            "form_build_id": form_id,
            "form_id": "waste_collection_information",
        }
        r = s.post(
            API_URL,
            headers=HEADERS,
            data=payload,
        )
        form_id = self.get_form_id(r.text)
        # soup = BeautifulSoup(r.text, "html.parser")
        # x = soup.find("input", {"name": "form_build_id"})
        # form_id = x.get("value")

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
            waste_date = table.find("td")[-1].text
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%d/%B/%Y").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.upper()),
                )
            )

        return entries
