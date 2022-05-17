from audioop import add
import datetime
import json

import requests
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Belmont City Council"
DESCRIPTION = "Source for Belmont City Council rubbish collection."
URL = "https://www.belmont.wa.gov.au/"
TEST_CASES = {
    "PETstock Belmont": {
        "post_code": "6104",
        "suburb": "Belmont",
        "street_name": "Abernethy Rd",
        "street_number": "196",
    },
    "Belgravia Medical Centre": {
        "post_code": "6105",
        "suburb": "Cloverdale",
        "street_name": "Belgravia St",
        "street_number": "374",
    },
    "IGA Rivervale": {
        "post_code": "6103",
        "suburb": "Rivervale",
        "street_name": "Kooyong Rd",
        "street_number": "126",
    },
}

class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):

        addressrequest = requests.get("https://www.belmont.wa.gov.au/api/intramaps/getaddresses?key="+str(self.street_number)+"%20"+self.street_name+"%20"+self.suburb+"%20"+str(self.post_code)).json()

        for array in addressrequest:
            mapkey = str(array["mapkey"])
            dbkey = str(array["dbkey"])
        

        mapdbkeyurl = "https://www.belmont.wa.gov.au/api/intramaps/getpropertydetailswithlocalgov?mapkey="+mapkey+"&dbkey="+dbkey
        
        collectionrequest = requests.get(mapdbkeyurl).json()

        data = collectionrequest["data"]

        entries = []

        entries.append(
            Collection(
                date=datetime.datetime.strptime(data["BinDayGeneralWasteFormatted"], "%Y-%m-%dT%H:%M:%S").date(),
                t="General Waste",
                icon="mdi:trash-can",
            )
        )

        entries.append(
            Collection(
                date=datetime.datetime.strptime(data["BinDayRecyclingFormatted"], "%Y-%m-%dT%H:%M:%S").date(),
                t="Recycling",
                icon="mdi:recycle",
            )
        )

        return entries
