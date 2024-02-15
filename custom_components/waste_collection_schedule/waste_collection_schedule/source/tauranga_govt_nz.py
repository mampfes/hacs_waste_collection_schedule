import json
from datetime import datetime
from typing import Dict, List, Tuple
from urllib.parse import quote, urlencode

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Tauranga City Council"
DESCRIPTION = "Source script for Tauranga City Council"
URL = "https://www.tauranga.govt.nz/"
TEST_CASES = {
    "121 Castlewold Drive": {"address": "121 Castlewold Drive"},
    "70 Santa Monica Drive": {"address": " 70 Santa Monica Drive"},
    "21 Wells Avenue": {"address": " 21 Wells Avenue"},
}

API_URL = "https://www.tauranga.govt.nz/living/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out"
ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Garden waste": "mdi:leaf",
    "Food scraps": "mdi:food-apple",
}


class Source:
    def __init__(self, address: str) -> None:
        self._address: str = address
        self._session: requests.Session = requests.Session()

    ADDRESS_URL = "https://www.tauranga.govt.nz/Services/SearchService.asmx/DoRIDStreetPredictiveSearch"
    WASTE_URL = "https://www.tauranga.govt.nz/living/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out"

    def fetch(self):
        addr_1, addr_2 = self.get_address_detail()
        form_data = self.generate_form_data(addr_1, addr_2)
        waste_response = self.get_waste_pickup_dates(form_data)

        return self.parse_waste_pickup_dates(waste_response)

    def get_address_detail(self) -> Tuple[str, str]:
        address_response = self._session.post(
            self.ADDRESS_URL,
            json={"prefixText": self._address, "count": 12, "contextKey": "test"},
            headers={"Content-Type": "application/json; charset=UTF-8"},
        ).json()

        if len(address_response.get("d")) == 0:
            raise Exception("Address not found within TCC records")

        # Parse address data from initial request
        address_dict = json.loads(address_response.get("d")[0])
        addr_1 = address_dict.get("First")
        addr_2 = address_dict.get("Second")

        return addr_1, addr_2

    def get_waste_pickup_dates(self, form_data: Dict[str, str]) -> requests.Response:
        pickup_date_response = self._session.post(
            self.WASTE_URL,
            data=form_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },
        )

        return pickup_date_response

    def generate_form_data(self, addr_1: str, addr_2: str) -> str:
        state_response = self._session.get(self.WASTE_URL)
        soup = BeautifulSoup(state_response.content, "html.parser")
        view_state = soup.find("input", attrs={"id": "__VIEWSTATE"})["value"]
        event_validation = soup.find("input", attrs={"id": "__EVENTVALIDATION"})[
            "value"
        ]

        form_data = {
            "dnn$ctr2863$MasterView$CollectionDaysv2$Address": addr_1,
            "dnn$ctr2863$MasterView$CollectionDaysv2$hdnValue": f"{addr_1}||{addr_2}",
            "__VIEWSTATE": view_state,
            "__EVENTVALIDATION": event_validation,
        }

        encoded_form_data = urlencode(form_data, quote_via=quote)

        return encoded_form_data

    def parse_waste_pickup_dates(
        self, pickup_date_response: requests.Response
    ) -> List[Collection]:
        soup = BeautifulSoup(pickup_date_response.text, "html.parser")
        bin_type_containers = soup.find_all("div", class_="binTypeContainer")

        entries = []

        for container in bin_type_containers:
            date = container.find("h5").text.strip()
            bin_types = [
                item.text
                for item in container.find_all("p")
                if item.find("span", class_="dot")
            ]
            if date == "Not subscribed":
                continue  # Skip waste types that aren't being paid for/subscribed to.
            else:
                current_date = datetime.now()
                pickup_datetime = datetime.strptime(date, "%A %d %B")

                if current_date.month == 12 and pickup_datetime.month == 1:
                    # Date responses have no year, handle adding a year and also year end/new year collections
                    pickup_date = pickup_datetime.replace(
                        year=datetime.now().year + 1
                    ).date()

                pickup_date = pickup_datetime.replace(year=datetime.now().year).date()

            for bin_type in bin_types:
                entries.append(
                    Collection(
                        date=pickup_date,
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type),
                    )
                )

        return entries
