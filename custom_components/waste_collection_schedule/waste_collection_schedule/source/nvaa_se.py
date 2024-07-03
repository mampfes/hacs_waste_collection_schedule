from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Norrtalje Vatten & Avfall"
DESCRIPTION = "Source for Norrtalje Vatten & Avfall waste collection services, Sweden."
URL = "https://sjalvservice.nvaa.se/"

API_URL = f"{URL}api/v1/integration/"

NEXT_COLLECTION_URL = f"{API_URL}getNextGarbageCollection"
FIND_ADDRESS_URL = f"{API_URL}findAddress"


TEST_CASES = {
    "Gustav Adolfs väg 24, Norrtälje": {"street_address": "Gustav Adolfs väg 24, Norrtälje"},
}



ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple",
    "Slam": "mdi:valve",
}



def parse_date(next_pickup_date):
    # Parse the date string into a datetime object
    # There are two possible date formats: specific days in Swedish and weeks
    # Specific date: Tisdag 4 juni 2024     
    # week: v10 2025

    if next_pickup_date.startswith("v"):
        # Parse week format
        week_number = int(next_pickup_date[1:].split()[0])
        year = int(next_pickup_date.split()[1])
        date_obj = datetime.strptime(f"{year}-W{week_number-1}-1", "%Y-W%W-%w").date()
    else:
        # Parse specific date format
        swedish_days = {
            "Måndag": "Monday",
            "Tisdag": "Tuesday",
            "Onsdag": "Wednesday",
            "Torsdag": "Thursday",
            "Fredag": "Friday",
            "Lördag": "Saturday",
            "Söndag": "Sunday",
        }
        swedish_months = {
            "januari": 1,
            "februari": 2,
            "mars": 3,
            "april": 4,
            "maj": 5,
            "juni": 6,
            "juli": 7,
            "augusti": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "december": 12,
        }
        day, day_number, month, year = next_pickup_date.split()
        day = swedish_days[day]
        month = swedish_months[month]
        date_obj = datetime.strptime(f"{year}-{month}-{day_number}", "%Y-%m-%d").date()    

    return date_obj

class Source:
    def __init__(self, street_address):
        self.street_address = street_address

    def fetch_building_id(self, session):
        
        search_payload = {"address": self.street_address}
        response = session.post(
            FIND_ADDRESS_URL,
            data=search_payload,
        )
        search_data = response.json()["results"]

        if len(search_data) == 0:
            raise ValueError(f"Search for address failed for {self.street_address}.")
        
        
        
        building_id = search_data[0].get("id")
        if not building_id:
            raise ValueError(f"Failed to get address ID for {self.street_address}.")

        return building_id
    
    def fetch_schedule_for_building_id(self, session, building_id):
        data = {"buildingId": building_id}

        response = session.post(NEXT_COLLECTION_URL, json=data)
        schedule_data = response.json()

        return schedule_data

    def format_schedule_data(self, schedule_data):
        entries = []
        for service in schedule_data:
            waste_type = service["product"]
            next_pickup_date = service["next_collection"]
            date_obj = parse_date(next_pickup_date)
            entries.append(
                Collection(
                    date=date_obj, t=waste_type, icon=ICON_MAP.get(waste_type)
                )
            )
        return entries


    def fetch(self):
        with requests.Session() as s:
            building_id = self.fetch_building_id(s)
            schedule_data = self.fetch_schedule_for_building_id(s, building_id)

        entries = self.format_schedule_data(schedule_data)
        

        return entries
