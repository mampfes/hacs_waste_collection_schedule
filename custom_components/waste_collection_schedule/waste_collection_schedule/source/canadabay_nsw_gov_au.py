import json
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.WasteInfo import (
    property_matches,
    same,
    street_number_suggestions,
)

TITLE = "City of Canada Bay Council"
DESCRIPTION = "Source for City of Canada Bay Council rubbish collection."
URL = "https://www.canadabay.nsw.gov.au"
TEST_CASES = {
    "Harry's Shed": {
        "suburb": "Concord",
        "street_name": "Gipps Street",
        "street_number": "1A",
    },
    "Five Dock Library": {
        "suburb": "Five Dock",
        "street_name": "Garfield Street",
        "street_number": "4-12",
    },
    "Dazed cafe": {
        "suburb": "Mortlake",
        "street_name": "Tennyson Road",
        "street_number": "76",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}
API_URL = "https://canada-bay.waste-info.com.au/api/v1"


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
            f"{API_URL}/localities.json",
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our suburb
        for item in data["localities"]:
            if same(item["name"], self.suburb):
                suburb_id = item["id"]
                break

        if suburb_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "suburb", self.suburb, [x["name"] for x in data["localities"]]
            )

        # Retrieve the streets in our suburb
        r = requests.get(
            f"{API_URL}/streets.json",
            params={"locality": suburb_id},
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our street
        for item in data["streets"]:
            if same(item["name"], self.street_name):
                street_id = item["id"]
                break

        if street_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name", self.street_name, [x["name"] for x in data["streets"]]
            )

        # Retrieve the properties in our street
        r = requests.get(
            f"{API_URL}/properties.json",
            params={"street": street_id},
            headers=HEADERS,
        )
        data = json.loads(r.text)

        # Find the ID for our property
        for item in data["properties"]:
            if property_matches(
                item["name"], self.street_number, self.street_name, self.suburb
            ):
                property_id = item["id"]
                break

        if property_id == 0:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_number",
                self.street_number,
                street_number_suggestions(
                    (x["name"] for x in data["properties"]), self.street_name
                ),
            )

        # Retrieve the upcoming collections for our property
        r = requests.get(
            f"{API_URL}/properties/{property_id}.json",
            params={
                "start": today,
                "end": nextmonth,
            },
            headers=HEADERS,
        )

        data = json.loads(r.text)

        entries = []

        for item in data:
            if "start" in item:
                collection_date = date.fromisoformat(item["start"])
                if (collection_date - today).days >= 0:
                    if item["event_type"] in ["recycle", "organic"]:
                        # Every collection day includes rubbish
                        entries.append(
                            Collection(
                                date=collection_date, t="Waste", icon="mdi:trash-can"
                            )
                        )
                        if item["event_type"] == "recycle":
                            entries.append(
                                Collection(
                                    date=collection_date,
                                    t="Recycling",
                                    icon="mdi:recycle",
                                )
                            )
                        if item["event_type"] == "organic":
                            entries.append(
                                Collection(
                                    date=collection_date, t="Organics", icon="mdi:leaf"
                                )
                            )
                    elif item["event_type"] == "clean_up":
                        entries.append(
                            Collection(
                                date=collection_date,
                                t="Bulk Household",
                                icon="mdi:couch",
                            )
                        )

        return entries
