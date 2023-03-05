import requests

from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mid-Sussex District Council"
DESCRIPTION = "Source for midsussex.gov.uk services for Mid-Sussex District Council, UK."
URL = "https://midsussex.gov.uk"

TEST_CASES = {
    "Test_001": {"house_name": "", "house_number": "6", "street": "Withypitts", "postcode": "RH10 4PJ"},
    "Test_002": {"house_name": "Oaklands", "house_number": "", "street": "Oaklands Road", "postcode": "RH16 1SS"},
    "Test_003":{"house_name": "", "house_number": 9, "street": "Bolnore Road", "postcode": "RH16 4AB"}
}

ICON_MAP = {
    "Garden bin collection": "mdi:leaf",
    "Rubbish bin collection": "mdi:trash-can",
    "Recycling bin collection": "mdi:recycle",
}

API_URL = "https://www.midsussex.gov.uk/waste-recycling/bin-collection/"

class Source:
    def __init__(self, house_name, house_number, street, postcode):
        self._house_name = str(house_name).upper()
        self._house_number = str(house_number)
        self._street = str(street).upper()
        self._postcode = str(postcode).upper()

    def fetch(self):
        s = requests.Session()

        if self._house_name == "":
            address = self._house_number + " " + self._street + " " + self._postcode
        else:
            address = self._house_name + "," + self._house_number + " " + self._street + " " + self._postcode

        payload = {
            "PostCodeStep.strAddressSearch": self._postcode,
            "AddressStep.strAddressSelect": address,
            "Next": "true",
            "StepIndex": "1",
        }

        # Seems to need a ufprt, so get that and then repeat query
        r0 = s.post(API_URL, data = payload)
        soup = BeautifulSoup(r0.text, features="html.parser")
        token = soup.find("input", {"name": "ufprt"}).get("value")
        payload.update({"ufprt": token})
        
        # Retrieve collection details
        r1 = s.post(API_URL, data = payload)
        soup = BeautifulSoup(r1.text, features="html.parser")
        tr = soup.findAll("tr")
        tr = tr[1:]  # remove header row 

        entries = []

        for td in tr:
            item = td.findAll("td")[1:]
            entries.append(
                Collection(
                    date=datetime.strptime(
                        item[1].text, "%A %d %B %Y").date(),
                    t=item[0].text,
                    icon=ICON_MAP.get(item[0].text),
                )
            )

        return entries

