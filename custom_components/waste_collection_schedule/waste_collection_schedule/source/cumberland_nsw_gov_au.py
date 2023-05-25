import json
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cumberland Council (NSW)"
DESCRIPTION = "Source for Cumberland Council (NSW) rubbish collection."
URL = "https://www.cumberland.nsw.gov.au"
TEST_CASES = {
    "Berala Community Centre": {
        "suburb": "Berala",
        "street_name": "Woodburn Road",
        "street_number": "98 to 104",
    },
    "McDonald's Auburn": {
        "suburb": "Auburn",
        "street_name": "Parramatta Road",
        "street_number": "116",
    },
    "Chickenlicious Guildford": {
        "suburb": "Guildford",
        "street_name": "Woodville Road",
        "street_number": 283,
    }
}

HEADERS = {"user-agent": "Mozilla/5.0"}


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
        nextmonth = today + timedelta(days=365)

        # Retrieve suburbs
        r = requests.get(
            "https://cumberland.waste-info.com.au/api/v1/localities.json", headers=HEADERS
        )
        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["localities"]:
            if item["name"] == self.suburb:
                suburb_id = item["id"]
                break

        if suburb_id == 0:
            return []

        # Retrieve the streets in our suburb
        r = requests.get(
            f"https://cumberland.waste-info.com.au/api/v1/streets.json?locality={suburb_id}",
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our street
        for item in data["streets"]:
            if item["name"] == self.street_name:
                street_id = item["id"]
                break

        if street_id == 0:
            return []

        # Retrieve the properties in our street
        r = requests.get(
            f"https://cumberland.waste-info.com.au/api/v1/properties.json?street={street_id}",
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our property
        for item in data["properties"]:
            if item["name"] == f"{self.street_number} {self.street_name} {self.suburb}":
                property_id = item["id"]
                break

        if property_id == 0:
            return []

        # Retrieve the upcoming collections for our property
        r = requests.get(
            f"https://cumberland.waste-info.com.au/api/v1/properties/{property_id}.json?start={today}&end={nextmonth}",
            headers=HEADERS,
        )

        data = json.loads(r.text)

        entries = []

        for item in data:
            if "start" in item:
                collection_date = date.fromisoformat(item["start"])
                if (collection_date - today).days >= 0:
                    # Only consider recycle and organic events
                    if item["event_type"] in ["recycle","organic"]:
                        # Every collection day includes rubbish
                        entries.append(
                            Collection(
                                date=collection_date, t="Rubbish", icon="mdi:trash-can"
                            )
                        )
                        if item["event_type"] == "recycle":
                            entries.append(
                                Collection(
                                    date=collection_date, t="Recycling", icon="mdi:recycle"
                                )
                            )
                        if item["event_type"] == "organic":
                            entries.append(
                                Collection(
                                    date=collection_date, t="Garden", icon="mdi:leaf"
                                )
                            )

        return entries
