import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Belmont City Council"
DESCRIPTION = "Source for Belmont City Council rubbish collection."
URL = "https://www.belmont.wa.gov.au/"
TEST_CASES = {
    "PETstock Belmont": {"address": "196 Abernethy Road Belmont 6104"},
    "Belgravia Medical Centre": {"address": "374 Belgravia Street Cloverdale 6105"},
    "IGA Rivervale": {"address": "126 Kooyong Road Rivervale 6103"},
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self):
        params = {"key": self._address}
        r = requests.get(
            "https://www.belmont.wa.gov.au/api/intramaps/getaddresses", params=params
        )
        r.raise_for_status()
        j = r.json()

        if len(j) == 0:
            raise Exception("address not found")

        if len(j) > 1:
            raise Exception("multiple addresses found")

        params = {"mapkey": j[0]["mapkey"], "dbkey": j[0]["dbkey"]}
        r = requests.get(
            "https://www.belmont.wa.gov.au/api/intramaps/getpropertydetailswithlocalgov",
            params=params,
        )
        r.raise_for_status()
        data = r.json()["data"]

        entries = []

        # get general waste
        date = datetime.datetime.strptime(
            data["BinDayGeneralWasteFormatted"], "%Y-%m-%dT%H:%M:%S"
        ).date()
        entries.append(
            Collection(
                date=date,
                t="General Waste",
                icon="mdi:trash-can",
            )
        )

        # get recycling
        date = datetime.datetime.strptime(
            data["BinDayRecyclingFormatted"], "%Y-%m-%dT%H:%M:%S"
        ).date()
        entries.append(
            Collection(
                date=date,
                t="Recycling",
                icon="mdi:recycle",
            )
        )

        return entries
