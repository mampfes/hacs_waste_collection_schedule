import datetime
import requests as request
import json
import logging
from waste_collection_schedule import Collection

_LOGGER = logging.getLogger(__name__)

TITLE = "Vestforbrænding" # Title will show up in README.md and info.md
DESCRIPTION = "Source for Vestforbrændning collection"  # Describe your source
URL = "https://selvbetjening.vestfor.dk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Home": {"streetName": "Kløvertoften", "number": "61", "zipCode": "2740"}
}

API_URL = "https://selvbetjening.vestfor.dk/Adresse/ToemmeDates"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "Haveaffald": "mdi:leaf",
    "Storskrald": "mdi:recycle",
    "Mad/Rest affald": "mdi:food",
    "Pap": "mdi:archive",
    "Papir/Plast \u0026 MDK": "mdi:bottle-soda",
    "Metal/Glas affald": "mdi:wrench",
    "Juletræer": "mdi:pine-tree",
}

ADRESS_LOOKUP_URL = "https://selvbetjening.vestfor.dk/Adresse/AddressByName"

class Source:
    def __init__(self, streetName, number, zipCode):
        self._streetName = streetName
        self._number = number
        self._zipCode = zipCode

    def fetch(self):
        entries = []  # List that holds collection schedule

        term = self._streetName + " " + self._number + ", " + self._zipCode

        _LOGGER.info("Fetching addressId from Vestforbrændning: " + term)
        addressResponse = request.get(ADRESS_LOOKUP_URL, params={"term": term, "numberOfResults": 1})
        
        addresses = json.loads(addressResponse.text)

        if len(addresses) == 0:
            _LOGGER.error("No address found for " + term)
            return entries
        addressId = addresses[0]["Id"]
        
        _LOGGER.info("Fetching data from Vestforbrændning")
        start_date = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
        end_date = (datetime.datetime.now() + datetime.timedelta(days=90)).strftime("%Y-%m-%dT%H:%M:%S%z")

        headers = {
            "Cookie": "addressId=" + str(addressId)
        }
        response = request.get(API_URL, params={"start": start_date, "end": end_date}, headers=headers)
        data = json.loads(response.text)
        
        for item in data:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(item["start"], "%Y-%m-%d").date(),  # Collection date
                    t=item["title"],  # Collection type
                    icon=ICON_MAP.get(item["title"]),  # Collection icon
                )
            )

        return entries
