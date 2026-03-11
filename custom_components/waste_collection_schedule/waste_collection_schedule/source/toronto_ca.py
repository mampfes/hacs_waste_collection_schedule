import csv
import json
from datetime import datetime, timedelta

import requests

from ..collection import Collection

TITLE = "Toronto (ON)"
DESCRIPTION = "Source for Toronto waste collection"
URL = "https://www.toronto.ca"

TEST_CASES = {
    "224 Wallace Ave": {"street_address": "224 Wallace Ave"},
    "324 Weston Rd": {"street_address": "324 Weston Rd"},
}

WASTE_CSV_URL = "https://www.toronto.ca/ext/swms/collection_calendar.csv"
WASTE_PROPERTY_LOOKUP_URL = "https://map.toronto.ca/cotgeocoder/rest/geocoder/suggest"
WASTE_SCHEDULE_LOOKUP_URL = (
    "https://map.toronto.ca/cotgeocoder/rest/geocoder/findAddressCandidates"
)

RECYCLE_PROPERTY_LOOKUP_URL = "https://ca-web.apigw.recyclecoach.com/zone-setup/address/multi?"
RECYCLE_PROPERTY_LOOKUP_CIRCMATONT = "CIRCMATONT:AJAX,ALGONQUINHIGHLANDS,AMARANTH,AMHERSTBURG,ARMOUR,BARRIE,BRAMPTON,BRANT,BRIGHTON,BROCK,BROCKVILLE,CALEDON,CAMBRIDGE,CARLETONPLACE,CARLING,CHATHAMKENT,CLARENCEROCKLAND,CLARINGTON,COBOURG,DYSARTETAL,EASTGARAFRAXA,ERIN,ESSEX,FORTERIE,GEORGIANBAY,GRANDVALLEY,GRIMSBY,GUELPHERAMOSA,HALDIMAND,HUNTSVILLE,KINGSVILLE,KITCHENER,LINCOLN,LONDON,LUCANBIDDULPH,MALAHIDE,MAPLETON,MARKHAM,MELANCTHON,MINDENHILLS,MINTO,MISSISSAUGA,MISSISSIPPIMILLS,MONO,MULMUR,MUSKOKALAKES,NEWBURY,NIAGARAFALLS,NIAGARAONTHELAKE,NORFOLK,NORTHDUMFRIES,OTTAWA,PELHAM,PETERBOROUGH,PICKERING,PORTCOLBORNE,PORTHOPE,PUSLINCH,SARNIA,SCUGOG,SEGUIN,SELWYN,SHELBURNE,SOUTHWOLD,STCATHARINES,TECUMSEH,TERRACEBAY,THOROLD,TIMMINS,TORONTO,TRENTLAKES,UXBRIDGE,VAUGHAN,WAINFLEET,WATERLOO,WELLAND,WELLESLEY,WELLINGTONNORTH,WESTLINCOLN,WILMOT,WOOLWICH"
RECYCLE_SCHEDULE_LOOKUP_URL = (
    "https://ca-web.apigw.recyclecoach.com/zone-setup/zone/schedules"
)

ICON_MAP = {
    "GreenBin": "mdi:compost",
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "YardWaste": "mdi:grass",
    "ChristmasTree": "mdi:pine-tree",
}

PICTURE_MAP = {
    "GreenBin": "https://www.toronto.ca/resources/swm_collection_calendar/img/greenbin.png",
    "Garbage": "https://www.toronto.ca/resources/swm_collection_calendar/img/garbagebin.png",
    "Recycling": "https://www.toronto.ca/resources/swm_collection_calendar/img/bluebin.png",
    "YardWaste": "https://www.toronto.ca/resources/swm_collection_calendar/img/yardwaste.png",
}

VALID_WASTE_TYPES = set(ICON_MAP) | set(PICTURE_MAP)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        """Main entry point to gather all collection entries."""
        entries = []
        with requests.Session() as session:
            # 1. Handle Recycling Data
            entries.extend(self._fetch_recycling_entries(session))
            
            # 2. Handle Waste Data
            entries.extend(self._fetch_waste_entries(session))
            
        return entries

    def _fetch_recycling_entries(self, session):
        """Logic for fetching and parsing recycling-specific schedules."""
        try:
            resp = session.get(
                RECYCLE_PROPERTY_LOOKUP_URL,
                params={"term": self._street_address, "projects": RECYCLE_PROPERTY_LOOKUP_CIRCMATONT}
            )
            results = resp.json().get("results", [])
            if not results:
                return []

            prop = results[0]
            zone_id = f"zone-{next(iter(prop['zones'].values()))}"
            
            sched_resp = session.get(
                RECYCLE_SCHEDULE_LOOKUP_URL,
                params={
                    "project_id": "CIRCMATONT",
                    "district_id": prop["district_id"],
                    "zone_id": zone_id
                },
                timeout=30
            )
            
            dates = self.extract_dates(sched_resp.json())
            return [self._create_collection(d, 'Recycling') for d in dates]
        except (requests.RequestException, KeyError, StopIteration):
            return []

    def _fetch_waste_entries(self, session):
        """Logic for fetching and parsing waste/trash-specific schedules."""
        entries = []
        # Step A: Get Property Key
        prop_json = session.get(WASTE_PROPERTY_LOOKUP_URL, params={
            "f": "json", "matchAddress": 1, "searchString": self._street_address
        }, timeout=30).json()
        
        key = self.get_first_result(prop_json, "KEYSTRING")
        if not key:
            return []

        # Step B: Get Area Cursor
        sched_json = session.get(WASTE_SCHEDULE_LOOKUP_URL, params={
            "keyString": key, "unit": "%", "areaTypeCode1": "RESW"
        }, timeout=30).json()
        
        cursor = self.get_first_result(sched_json, "AREACURSOR1")
        if not cursor:
            return []

        area_name = cursor["array"][0]["AREA_NAME"]
        
        # Step C: Parse CSV Schedule
        csv_resp = session.get(WASTE_CSV_URL, timeout=30)
        reader = csv.DictReader(csv_resp.text.splitlines())
        reader.fieldnames = [n.strip() if n else n for n in reader.fieldnames]
        
        # Identify dynamic keys
        cal_key = next((k for k in reader.fieldnames if k.lower() == "calendar"), None)
        week_key = next((k for k in reader.fieldnames if "week" in k.lower() and "start" in k.lower()), None)

        if not (cal_key and week_key):
            return []

        days_map = "MTWRFSX"
        for row in reader:
            if not row.get(cal_key, "").startswith(area_name):
                continue
            
            base_date = datetime.strptime(row[week_key], "%Y-%m-%d")
            for w_type in VALID_WASTE_TYPES:
                day_code = row.get(w_type)
                if not day_code is None and day_code in days_map:
                    offset = days_map.index(day_code) - base_date.weekday()
                    actual_date = (base_date + timedelta(days=offset)).date()
                    entries.append(self._create_collection(actual_date, w_type))
        
        return entries

    def _create_collection(self, date_obj, collection_type):
        """Helper to standardize Collection object creation."""
        return Collection(
            date_obj,
            collection_type,
            picture=PICTURE_MAP.get(collection_type),
            icon=ICON_MAP.get(collection_type)
        )

    def get_first_result(self, json_data, key):
        result = json_data.get("result", {})
        rows = result.get("rows", [])

        if not rows:
            return None

        return rows[0].get(key)

    def extract_dates(self, json_data):
        date_objects = []
        
        # Iterate through the nested structure
        for year_entry in json_data.get("DATA", []):
            for month_entry in year_entry.get("months", []):
                for event in month_entry.get("events", []):
                    # Grab the date string
                    date_str = event.get("date")
                    if date_str:
                        # Convert to python date object and append to list
                        date_objects.append(datetime.fromisoformat(date_str).date())
                    
        return date_objects
