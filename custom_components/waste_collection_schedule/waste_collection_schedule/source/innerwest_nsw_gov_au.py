import json
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Inner West Council (NSW)"
DESCRIPTION = "Source for Inner West Council (NSW) rubbish collection."
URL = "https://www.innerwest.nsw.gov.au"
TEST_CASES = {
    "Random Marrickville address": {
        "suburb": "Tempe",
        "street_name": "Princes Highway",
        "street_number": "813",
    },
    "Random Leichhardt address": {
        "suburb": "Rozelle",
        "street_name": "Darling Street",
        "street_number": "597",
    },
    "Random Ashfield address": {
        "suburb": "Summer Hill",
        "street_name": "Lackey Street",
        "street_number": "29",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}
# Inner West council merged 3 existing councils, but still hasn't merged their
# data so details need to be found from one of three different databases.
APIS = [
    "https://leichhardt.waste-info.com.au/api/v1",
    "https://marrickville.waste-info.com.au/api/v1",
    "https://ashfield.waste-info.com.au/api/v1",
]

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
        nextmonth = today + timedelta(30)
        council_api = ""

        # Retrieve suburbs and council API
        for api in APIS:
            r = requests.get(f"{api}/localities.json", headers=HEADERS)
            data = json.loads(r.text)
            for item in data["localities"]:
                if item["name"] == self.suburb:
                    council_api = api
                    suburb_id = item["id"]
                    break
            if council_api:
                break

        if suburb_id == 0:
            return []

        # Retrieve the streets in our suburb
        r = requests.get(
            f"{council_api}/streets.json?locality={suburb_id}",
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
            f"{council_api}/properties.json?street={street_id}",
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
            f"{council_api}/properties/{property_id}.json?start={today}&end={nextmonth}",
            headers=HEADERS,
        )

        data = json.loads(r.text)

        entries = []

        for item in data:
            event_type = item.get("event_type")
            if not event_type:
                continue

            icon = ICON_MAP.get(event_type)

            if "dow" in item or "daysOfWeek" in item:
                # Recurring weekly collection: the API returns a single entry with a
                # start_date and day-of-week info rather than listing each occurrence.
                # Expand it into individual weekly entries across the window.
                if "start_date" not in item:
                    continue
                collection_date = date.fromisoformat(item["start_date"])
                # Ensure we start from today or later
                if collection_date < today:
                    collection_date = today
                while collection_date <= nextmonth:
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=event_type,
                            icon=icon,
                        )
                    )
                    collection_date += timedelta(7)
            else:
                # Single-occurrence collection: use the explicit start date
                key = (
                    "start"
                    if "start" in item
                    else "start_date" if "start_date" in item else None
                )
                if key is None:
                    continue
                collection_date = date.fromisoformat(item[key])
                if (collection_date - today).days >= 0:
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=event_type,
                            icon=icon,
                        )
                    )

        return entries
