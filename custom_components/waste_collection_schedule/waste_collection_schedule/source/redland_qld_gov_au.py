import json
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Redland City Council (QLD)"
DESCRIPTION = "Source for Redland City Council (QLD) rubbish collection."
URL = "https://www.redland.qld.gov.au"
TEST_CASES = {
    "Mount Cotton": {
        "suburb": "Mount Cotton",
        "street_name": "Mount Cotton Road",
        "street_number": "1,261",
    },
    "Random Redland Bay": {
        "suburb": "Redland Bay",
        "street_name": "Boundary Street",
        "street_number": "1",
    },
    "Random Victoria Point": {
        "suburb": "Victoria Point",
        "street_name": "Colburn Avenue",
        "street_number": "25",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}

API = "https://redland.waste-info.com.au/api/v1"

ICON_MAP = {
    "waste": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "organic": "mdi:leaf",
}


class Source:
    def __init__(self, suburb, street_name, street_number):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        suburb_id = 0
        street_id = 0
        property_id = 0
        today = date.today()
        nextyear = today + timedelta(365)

        # Retrieve suburbs
        r = requests.get(f"{API}/localities.json", headers=HEADERS)
        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["localities"]:
            if item["name"] == self.suburb:
                suburb_id = item["id"]
                break

        if suburb_id == 0:
            #return []
            raise Exception(f"Surburb '{self.suburb}' not found")

        # Retrieve the streets in our suburb
        r = requests.get(
            f"{API}/streets.json?locality={suburb_id}",
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our street
        for item in data["streets"]:
            if item["name"] == self.street_name:
                street_id = item["id"]
                break

        if street_id == 0:
            #return []
            raise Exception(f"Street '{self.street_name}' not found")

        # Retrieve the properties in our street
        r = requests.get(
            f"{API}/properties.json?street={street_id}",
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our property
        for item in data["properties"]:
            if item["name"] == f"{self.street_number} {self.street_name} {self.suburb}":
                property_id = item["id"]
                break

        if property_id == 0:
            #return []
            raise Exception(f"{self.street_number} {self.street_name} {self.suburb} not found")

        # Retrieve the upcoming collections for our property
        r = requests.get(
            f"{API}/properties/{property_id}.json?start={today}&end={nextyear}",
            headers=HEADERS,
        )

        data = json.loads(r.text)

        entries = []

        for item in data:
            if "start" not in item:
                continue

            collection_date = date.fromisoformat(item["start"])
            if (collection_date - today).days < 0:
                continue
            # Only consider recycle and organic events
            if item["event_type"] not in ["recycle", "organic"]:
                continue
            # Every collection day includes rubbish
            entries.append(
                Collection(date=collection_date, t="Rubbish", icon="mdi:trash-can")
            )
            if item["event_type"] == "recycle":
                entries.append(
                    Collection(date=collection_date, t="Recycling", icon="mdi:recycle")
                )
            if item["event_type"] == "organic":
                entries.append(
                    Collection(date=collection_date, t="Garden", icon="mdi:leaf")
                )

        return entries
