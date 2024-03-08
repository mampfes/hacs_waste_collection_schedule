import urllib.parse
import datetime
import json
import json
import requests
import argparse
import logging

from waste_collection_schedule import Collection

TITLE = "Hornsby Shire Council"
DESCRIPTION = "Source for Hornsby Shire Council."
URL = "https://hornsby.nsw.gov.au/"
TEST_CASES = {
    "randomHouse1": {
        "property_id": "306767"
    },
     "randomHouse2": {
        "property_id": "304613"
    }
}



API_URL = "https://hscapi.teststuffs.com/"
API_TOKEN = "fGygCt3dzKol9zVuYrzltPPrBPMIhYeQhGWPpGx13hWp2DpJsHF1al1vy6yZMRYw"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Yellow": "mdi:recycle",
    "Green": "mdi:leaf",
}

TONIGHT = False

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, property_id):
        self.property_id = property_id

    def fetch(self):
        s = requests.Session()
        payload = {
            "token": API_TOKEN,
            "property_id": self.property_id
        }
        response = s.post(API_URL, data=json.dumps(payload))
        data = json.loads(response.text)

        entries = []
        bulk_waste = data['bulk_dates']
        for date in bulk_waste:
            real_date = datetime.datetime.strptime(date, "%d/%m/%Y").date()
            entries.append(Collection(date=real_date, t="Bulky Waste", icon="mdi:delete"))
        collection_day = data['bins']['day']
        green_collection_date = datetime.datetime.strptime(data['bins']['next_green'], "%d/%m/%Y").date()
        yellow_collection_date = datetime.datetime.strptime(data['bins']['next_yellow'], "%d/%m/%Y").date()
        bin_this_week = data['bins']['this_week']
        entries.append(Collection(date=green_collection_date, t="Green Waste", icon=ICON_MAP.get("Green")))
        entries.append(Collection(date=yellow_collection_date, t="Recycling", icon=ICON_MAP.get("Yellow")))
        entries.append(Collection(date=yellow_collection_date, t="General Waste", icon=ICON_MAP.get("Refuse")))
        entries.append(Collection(date=green_collection_date, t="General Waste", icon=ICON_MAP.get("Refuse")))
        if TONIGHT:
            entries.append(Collection(date=green_collection_date-datetime.timedelta(days=1), t="Green Waste Tonight", icon=ICON_MAP.get("Green")))
            entries.append(Collection(date=yellow_collection_date-datetime.timedelta(days=1), t="Recycling Tonight", icon=ICON_MAP.get("Yellow")))
            entries.append(Collection(date=yellow_collection_date-datetime.timedelta(days=1), t="General Waste Tonight", icon=ICON_MAP.get("Refuse")))
            entries.append(Collection(date=green_collection_date-datetime.timedelta(days=1), t="General Waste Tonight", icon=ICON_MAP.get("Refuse")))

        return entries
