import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mid-Sussex District Council"
DESCRIPTION = "Source for midsussex.gov.uk services for Mid-Sussex District Council, UK."
URL = "https://midsussex.gov.uk"

TEST_CASES = {
    "Test_001": {"house_number": "9", "street": "BOLNORE ROAD", "postcode": "RH16 4AB"}
    # "Test_001": {"uprn": "100030011612"},
    # "Test_002": {"uprn": "100030011654"},
    # "test_003": {"uprn": 100030041980}
}

ICON_MAP = {
    "Garden bin collection": "mdi:leaf",
    "Rubbish bin collection": "mdi:trash-can",
    "Recyclng bin collection": "mdi:recycling",
}

API_URL = "https://www.midsussex.gov.uk/waste-recycling/bin-collection/"

class Source:
    def __init__(self, house_name, house_number, street, postcode):
        self._house_name = str(house_name)
        self._house_number = str(house_number)
        self._street = str(street)
        self._postcode = str(postcode)

    def fetch(self):
        s = requests.Session()

        if self._house_name:
            full_address = self._house_name + ", " + self._house_number + " " + self._street + " " + self._postcode
        else:
            full_address = self._house_number + " " + self._street + " " + self._postcode

        payload = {
            "PostCodeStep.strAddressSearch": postcode,
            "AddressStep.strAddressSelect": full_address,
            "Next": "true",
            "StepIndex": "1",
        }

        # Seems to need a ufprt, so get that and then repeat query
        r0 = s.post(URL, data = payload)
        soup = BeautifulSoup(r0.text, features="html.parser")
        token = soup.find("input", {"name": "ufprt"}).get("value")
        payload.update({"ufprt": token})
        r1 = s.post(URL, data = payload)

        soup = BeautifulSoup(r1.text, features="html.parser")
        tr = soup.findAll("tr")
        tr = x[1:]  # remove header row 

        entries = []

        for td in tr:
            item = td.findAll("td")[1:]
            entries.append(
                Collection(
                    date=datetime.strptime(
                        item[1], "%A %d %B %Y").date(),
                    t=item[0],
                    icon=ICON_MAP.get(item[0]),
                )
            )

        return entries

        # Monday 06 March 2023

