from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Maribyrnong Council"
DESCRIPTION = "Source for Maribyrnong Council (VIC) rubbish collection."
URL = "https://www.maribyrnong.vic.gov.au/Residents/Bins-and-recycling"
TEST_CASES = {
    "Random address": {
        "suburb": "Footscray",
        "street_name": "Ballarat Rd",
        "street_number": "70-100",
    }
}

HEADERS = {"user-agent": "Mozilla/5.0"}

ICON_MAP = {
    "recycle": "mdi:recycle",
    "organic": "mdi:leaf",
}


class Source:
    def __init__(self, suburb, street_name, street_number):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        # Retrieve suburbs
        r = requests.get(
            "https://maribyrnong.waste-info.com.au/api/v1/localities.json",
            headers=HEADERS,
        )
        data = r.json()

        # Find the ID for our suburb
        suburb_id = None
        for item in data["localities"]:
            if item["name"] == self.suburb:
                suburb_id = item["id"]
                break

        if suburb_id is None:
            raise Exception("suburb not found")

        # Retrieve the streets in our suburb
        params = {"locality": suburb_id}
        r = requests.get(
            "https://maribyrnong.waste-info.com.au/api/v1/streets.json",
            headers=HEADERS,
            params=params,
        )
        data = r.json()

        # Find the ID for our street
        street_id = None
        for item in data["streets"]:
            if item["name"] == self.street_name:
                street_id = item["id"]
                break

        if street_id is None:
            raise Exception("street_name not found")

        # Retrieve the properties in our street
        params = {"street": street_id}
        r = requests.get(
            "https://maribyrnong.waste-info.com.au/api/v1/properties.json",
            headers=HEADERS,
            params=params,
        )
        data = r.json()

        # Find the ID for our property
        property_id = None
        for item in data["properties"]:
            if item["name"] == f"{self.street_number} {self.street_name} {self.suburb}":
                property_id = item["id"]
                break

        if property_id is None:
            raise Exception("street_number not found")

        # Retrieve the upcoming collections for our property
        today = date.today()
        params = {"start": today, "end": today + timedelta(days=365)}
        r = requests.get(
            f"https://maribyrnong.waste-info.com.au/api/v1/properties/{property_id}.json",
            headers=HEADERS,
            params=params,
        )

        data = r.json()

        entries = []

        for item in data:
            if "start" in item:
                collection_date = date.fromisoformat(item["start"])
                if (collection_date - today).days >= 0:
                    waste_type = item["event_type"]

                    # Only consider recycle and organic events
                    if waste_type in ["recycle", "organic"]:
                        # Every collection day includes rubbish
                        entries.append(Collection(date=collection_date, t="rubbish"))

                        entries.append(
                            Collection(
                                date=collection_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )

        return entries
