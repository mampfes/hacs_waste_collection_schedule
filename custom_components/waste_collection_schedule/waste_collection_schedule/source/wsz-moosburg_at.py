import datetime
import requests
import json
from waste_collection_schedule import Collection

TITLE = "WSZ Moosburg"
DESCRIPTION = "Source for WSZ Moosburg/Kärnten, including Moosburg, Pörtschach, Techelsberg"
URL = "https://wsz-moosburg.at/calendar"
TEST_CASES = {
    "Moosburg_Obergöriach_Obergöriach": {
      "address_id": 70265
    },
    "Moosburg_Moosburg_Pestalozzistr": {
      "address_id": 70082
    },
    "Pörtschach_10OktoberStr_10OktoberStr": {
      "address_id": 69866
    },
    "Techelsberg_SüdlichDerBahn-BahnhofTöschlingBisSaagNr-19": {
      "address_id": 69980
    }
}

class Source:
    def __init__(self, address_id): # argX correspond to the args dict in the source configuration
        self.address_id = address_id

    def fetch(self):
        r = requests.get(f"https://wsz-moosburg.at/api/trash/{self.address_id}")
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
