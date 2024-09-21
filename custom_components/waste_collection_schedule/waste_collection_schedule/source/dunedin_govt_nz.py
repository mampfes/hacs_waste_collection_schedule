from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "Dunedin District Council"
DESCRIPTION = "Source for Dunedin District Council Rubbish & Recycling collection."
URL = "https://www.dunedin.govt.nz/"
TEST_CASES = {
    # "No Collection": {"address": "3 Farm Road West Berwick"},  # Useful for troubleshooting, elicits a "No Collection" response from website
    "Calendar 1": {"address": "5 Bennett Road Ocean View"},
    "Calendar 2": {"address": "2 Council Street Dunedin"},
    # "All Week": {"address": "118 High Street"}, # Does not have a collection schedule using the new API
    "Collection 'c'": {"address": "2 - 90 Harbour Terrace Dunedin"},
}
DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "RED BIN": "mdi:trash-can",
    "BLUE BIN": "mdi:bottle-soda",
    "YELLOW BIN": "mdi:recycle",
    "GREEN BIN": "mdi:leaf",
}

# To keep compatibility with the old version of this source and not break existing sensors
OLD_BIN_MAP = {
    "REC": "YELLOW BIN",
    "GLA": "BLUE BIN",
    "REF": "RED BIN",
    "FOD": "GREEN BIN",
}

API_URL = "https://environz-api.azurewebsites.net/api/dcc/nextservicedate"
API_KEY = "F9qPiSASucQZRqKi92rttnnfZ4d8cZNh8RfTVSpQ2it2AzFuMu13mA=="


class Source:
    def __init__(self, address):
        self._address = str(address).strip()
        split = self._address.split("-")
        if len(split) > 1 and split[0].strip().isdigit():
            split = [split[0].strip() + "/" + split[1].strip(), *split[2:]]
            self._address = "-".join(split)

    def fetch(self):
        end_date = (datetime.now() + timedelta(days=365)).strftime("%d/%m/%Y")
        params = {
            "code": API_KEY,
            "address": self._address,
            "endDate": end_date,
            "postcode": "",
        }

        r = requests.get(API_URL, params=params)
        if r.status_code == 400:
            raise Exception(
                "Invalid address or no collection schedule for this address, make sure the address matches an address, that has a schedule in the DCC Kerbside Collection app."
            )

        r.raise_for_status()

        data = r.json()

        entries = []
        for key, value in data.items():
            if not key.startswith("route") or not value:
                continue
            collection_type = key.removeprefix("route").strip()
            collection_type = OLD_BIN_MAP.get(collection_type, collection_type)
            for date in value.values():
                entries.append(
                    Collection(
                        date=datetime.strptime(date, "%d/%m/%Y").date(),
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type.upper()),
                    )
                )
        return entries
