import datetime
import json
import requests

from waste_collection_schedule import Collection

TITLE = "Port Stephens Council"
DESCRIPTION = "Source for Port Stephens Council waste collection."
URL = "https://www.portstephens.nsw.gov.au/u"
TEST_CASES = {
    "randomHouse": {
        "suburb": "Soldiers Point",
        "street_name": "Lyndel Close",
        "street_number": "9",
    }
}


API_BASE_URL = "https://port-stephens.waste-info.com.au/api/v1/" 

API_URLS = {
    "Localities": f"{API_BASE_URL}localities.json",
    "Streets": f"{API_BASE_URL}streets.json?locality=",
    "Properties": f"{API_BASE_URL}properties.json?street",
    "Collection": f"{API_BASE_URL}properties/",#31198.json?start=2023-12-31T13:00:00.000Z&end=2024-12-30T13:00:00.000Z"
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

ICON_MAP = {
    "general": "mdi:trash-can",
    "special": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "organic": "mdi:leaf",
}

ROUNDS = {
    "general": "General Waste",
    "recycle": "Recycling",
    "organic": "Green Waste",
}

TRACKED_EVENTS = [
    "general","recycle","organic","special"
]

class Source:
    def __init__(
        self, suburb: str, street_name: str, street_number: str
    ):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number
        self.street_address = f"{street_number} {street_name} {suburb}".lower()

    def fetch(self):

        locality_id = 0
        street_id = 0
        property_id = 0
        this_year = datetime.datetime.now().year
        last_year = this_year - 1
        entries = []

        request = requests.Session()
        locality_data = request.get(API_URLS["Localities"], headers = HEADERS)
        localities = json.loads(locality_data.text)
        #print(localities)
        for locality in localities["localities"]:
            if locality["name"] == self.suburb:
                locality_id = locality["id"]
        #        print(f"Locality ID: {locality_id}")
                break
        street_data = request.get(API_URLS["Streets"] + str(locality_id), headers = HEADERS)
        streets = json.loads(street_data.text)
        #print(streets)
        for street in streets["streets"]:
            if street["name"] == self.street_name:
                street_id = street["id"]
        #        print(f"Street ID: {street_id}")
                break
        property_data = request.get(API_URLS["Properties"] + str(street_id), headers = HEADERS)
        properties = json.loads(property_data.text)
        #print(properties)
        for property in properties["properties"]:
            if property["name"].lower() == self.street_address:
                property_id = property["id"]
        #        print(f"Property ID: {property_id}")
                break
        property_url = API_URLS["Collection"] + str(property_id) + f".json?start={last_year}-12-31T13:00:00.000Z&end={this_year}-12-30T13:00:00.000Z"
        collection_data = requests.get(property_url, headers = HEADERS)
        collections = json.loads(collection_data.text)
        #print(collections)
        for entry in collections:
            if "property" in entry:
                continue
            event_type = entry["event_type"]
            date = datetime.datetime.strptime(entry["start"], "%Y-%m-%d").date()
            if event_type == "special":
                event_name = entry["name"]
            else:
                event_name = ROUNDS.get(event_type)
            if event_type in TRACKED_EVENTS:
                entries.append(Collection(date=date, t=event_name, icon=ICON_MAP.get(event_type)))

        return entries
