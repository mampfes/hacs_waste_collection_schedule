import datetime
import requests
import json
from waste_collection_schedule import Collection

TITLE = "WSZ Moosburg"
DESCRIPTION = "Source for WSZ Moosburg/Kärnten, including Moosburg, Pörtschach, Techelsberg"
URL = "https://wsz-moosburg.at/calendar"
TEST_CASES = {
    "Address_Id_Moosburg_Obergöriach_Obergöriach": {
      "address_id": 70265
    },
    "Address_Id_Moosburg_Moosburg_Pestalozzistr": {
      "address_id": 70082
    },
    "Address_Id_Pörtschach_10OktoberStr_10OktoberStr": {
      "address_id": 69866
    },
    "Address_Id_Techelsberg_SüdlichDerBahn-BahnhofTöschlingBisSaagNr-19": {
      "address_id": 69980
    },
    "Address_Data_Moosburg_Obergöriach_Obergöriach": {
      "municipal": "Moosburg",
      "address": "Obergöriach",
      "street": "Obergöriach"
    },
    "Address_Data_Moosburg_Moosburg_Pestalozzistr": {
      "municipal": "Moosburg",
      "address": "Moosburg",
      "street": "Pestalozzistraße"
    },
    "Address_Data_Pörtschach_10OktoberStr_10OktoberStr": {
      "municipal": "Pörtschach",
      "address": "10.-Oktober-Straße",
      "street": "10.-Oktober-Straße"
    },
    "Address_Data_Techelsberg_SüdlichDerBahn-BahnhofTöschlingBisSaagNr-19": {
      "municipal": "Techelsberg",
      "address": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19",
      "street": "Südlich der Bahn: Bahnhof Töschling bis Saag Nr. 19"
    }
}

class Source:
    def __init__(self, **args):
        if len(args) < 1:
            print("Too few arguments")
        elif args.get("address_id"):
            self.address_id = args.get("address_id")
        elif len(args) > 2 and args.get("municipal") and args.get("address") and args.get("street"):
            self.municipal = args.get("municipal")
            self.address = args.get("address")
            self.street = args.get("street")
        else:
            print(f"Something unexpected happened")

    def fetch_by_address_id(self, address_id):
        r = requests.get(f"https://wsz-moosburg.at/api/trash/{address_id}")
        trashResponse = json.loads(r.text)

        entries = []
        for entry in trashResponse:
            entries.append(
              Collection(
                datetime.datetime.strptime(entry['start'], "%Y-%m-%d").date(),
                entry['title']
              )
            )

        return entries

    def get_address_id_from_address(self, municipal, address, street):
        MUNICIPAL_CHOICES = {
            "Moosburg": "20421",
            "Pörtschach": "20424",
            "Techelsberg": "20435"
        }
        municipal_id = MUNICIPAL_CHOICES[municipal]

        r = requests.get(f"https://wsz-moosburg.at/api/address/{municipal_id}")
        addressData = json.loads(r.text)['address']
        address = [x for x in addressData if x['address']['name'] == address][0]['address']

        # Some addresses have more streets, some have only 1 street, some have none.
        # Additional request only needed if at least one street will be there to select,
        # otherwise the final area ID is already returned in the address request.
        if int(address['sub']) > 0:
            r = requests.get(f"https://wsz-moosburg.at/api/address/{municipal_id}/{address['id']}")
            streetData = json.loads(r.text)['address']
            street = [x for x in streetData if x['address']['name'] == street][0]['address']
            return street['id']
        else:
            return address['id']

    def fetch(self):
        if not hasattr(self, "address_id") and hasattr(self, "municipal") and hasattr(self, "address") and hasattr(self, "street"):
            self.address_id = self.get_address_id_from_address(self.municipal, self.address, self.street)
            return self.fetch()
        if hasattr(self, "address_id"):
            return self.fetch_by_address_id(self.address_id)

        return []
