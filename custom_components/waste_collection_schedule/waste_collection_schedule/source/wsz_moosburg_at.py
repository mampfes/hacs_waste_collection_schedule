import datetime
import json

import requests
from waste_collection_schedule import Collection

TITLE = "WSZ Moosburg"
DESCRIPTION = (
    "Source for WSZ Moosburg/Kärnten, including Moosburg, Pörtschach, Techelsberg"
)
URL = "https://wsz-moosburg.at"
TEST_CASES = {
    "Id: Moosburg, Obergöriach": {"address_id": 70265},
    "Id: Moosburg, Pestalozzistr": {"address_id": 70082},
    "Id: Pörtschach, 10. OktoberStr": {"address_id": 69866},
    "Id: Techelsberg, Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19": {
        "address_id": 69980
    },
    "Full: Moosburg, Obergöriach": {
        "municipal": "Moosburg",
        "address": "Obergöriach",
        "street": "Obergöriach",
    },
    "Full: Moosburg, Pestalozzistr": {
        "municipal": "Moosburg",
        "address": "Moosburg",
        "street": "Pestalozzistraße",
    },
    "Full: Pörtschach, 10. OktoberStr": {
        "municipal": "Pörtschach",
        "address": "10.-Oktober-Straße",
        "street": "10.-Oktober-Straße",
    },
    "Data: Techelsberg, Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19": {
        "municipal": "Techelsberg",
        "address": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19",
        "street": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19",
    },
}

MUNICIPAL_CHOICES = {
    "Moosburg": "20421",
    "Pörtschach": "20424",
    "Techelsberg": "20435",
}


class Source:
    def __init__(self, **args):
        if len(args) == 1:
            self._address_id = args["address_id"]
        elif len(args) == 3:
            self._address_id = self.get_address_id_from_address(
                args["municipal"], args["address"], args["street"]
            )
        else:
            raise Exception("Invalid argument count")

    def fetch(self):
        r = requests.get(f"https://wsz-moosburg.at/api/trash/{self._address_id}")
        r.raise_for_status()

        trashResponse = json.loads(r.text)

        entries = []
        for entry in trashResponse:
            entries.append(
                Collection(
                    datetime.datetime.strptime(entry["start"], "%Y-%m-%d").date(),
                    entry["title"],
                )
            )

        return entries

    def get_address_id_from_address(self, municipal, address, street):
        municipal_id = MUNICIPAL_CHOICES[municipal]

        r = requests.get(f"https://wsz-moosburg.at/api/address/{municipal_id}")
        addressData = json.loads(r.text)["address"]
        address = [x for x in addressData if x["address"]["name"] == address][0][
            "address"
        ]

        # Some addresses have more streets, some have only 1 street, some have none.
        # Additional request only needed if at least one street will be there to select,
        # otherwise the final area ID is already returned in the address request.
        if int(address["sub"]) > 0:
            r = requests.get(
                f"https://wsz-moosburg.at/api/address/{municipal_id}/{address['id']}"
            )
            streetData = json.loads(r.text)["address"]
            street = [x for x in streetData if x["address"]["name"] == street][0][
                "address"
            ]
            return street["id"]
        else:
            return address["id"]
