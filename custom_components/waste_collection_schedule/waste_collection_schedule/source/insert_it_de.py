import json
import requests
import urllib

from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.InsertITDe import SERVICE_MAP
from waste_collection_schedule.service.ICS import ICS


TITLE = "Insert IT Apps"
DESCRIPTION = "Source for Apps by Insert IT"
URL = "https://insert-infotech.de/"
COUNTRY = "de"


def EXTRA_INFO():
    return [{"title": s["title"], "url": s["url"]} for s in SERVICE_MAP]

TEST_CASES = {
    "Offenbach Address": {
        "municipality": "Offenbach",
        "street": "Kaiserstraße",
        "hnr": 1
    },
    "Offenbach Location ID": {
        "municipality": "Offenbach",
        "location_id": 7036
    },
    "Mannheim Address": {
        "municipality": "Mannheim",
        "street": "A 3",
        "hnr": 1
    },
    "Mannheim Location ID": {
        "municipality": "Mannheim",
        "location_id": 430650
    }
}


MUNICIPALITIES = {
    "Hattingen": "BmsAbfallkalenderHattingen",
    "Herne": "BmsAbfallkalenderHerne",
    "Kassel": "BmsAbfallkalenderKassel",
    "Krefeld": "BmsAbfallkalenderKrefeld",
    "Mannheim": "BmsAbfallkalenderMannheim",
    "Offenbach": "BmsAbfallkalenderOffenbach",
}

ICON_MAP = {
    "Offenbach": {
        "Restmüll": {"icon": "mdi:trash-can", "name": "Restmüll"},
        "Biomüll": {"icon": "mdi:leaf", "name": "Biomüll"},
        "DSD": {"icon": "mdi:recycle", "name": "DSD"},
        "Altpapier": {"icon": "mdi:package-variant", "name": "Altpapier"},
    },
    "Mannheim": {
        "Rest": {"icon": "mdi:trash-can", "name": "Restmüll"},
        "Wertstoff": {"icon": "mdi:recycle", "name": "Sack/Tonne gelb"},
        "Bio": {"icon": "mdi:leaf", "name": "Biomüll"},
        "Papier": {"icon": "mdi:package-variant", "name": "Altpapier"},
        "Grünschnitt": {"icon": "mdi:leaf", "name": "Grünschnitt"},
    }
}

REGEX_MAP = {
    "Hattingen": r"Leerung:\s+(.*)\s+\(.*\)",
    "Herne": r"Leerung:\s+(.*)\s+\(.*\)",
    "Kassel": r"Leerung:\s+(.*)\s+\(.*\)",
    "Krefeld": r"Leerung:\s+(.*)\s+\(.*\)",
    "Mannheim": r"Leerung:\s+(.*)",
    "Offenbach": r"Leerung:\s+(.*)\s+\(.*\)",
}


class Source:
    def __init__(self, municipality, street=None, hnr=None, location_id=None):
        self._municipality = municipality
        self._street = street
        self._hnr = hnr
        self._location = location_id

        # Check if municipality is in list
        municipalities = MUNICIPALITIES
        if municipality not in municipalities:
            raise Exception(f"municipality '{municipality}' not found")
        
        self._api_url = f"https://www.insert-it.de/{municipalities[municipality]}"
        self._ics = ICS(regex=REGEX_MAP.get(municipality))


        # Check if at least either location_id is set or both street and hnr are set
        if not ((location_id is not None) or (street is not None and hnr is not None)):
            raise Exception("At least either location_id should be set or both street and hnr should be set.")
        
        self._uselocation = location_id is not None


    def get_street_id(self):
        """Return ID of matching street"""

        s = requests.Session()
        params = {"text": self._street}

        r = s.get(f"{self._api_url}/Main/GetStreets", params=params)
        r.raise_for_status()
        r.encoding = "utf-8"

        result = json.loads(r.text)
        if not result:
            raise Exception(f"No street found for Street {self._street}")

        for element in result:
            if element["Name"] == self._street:
                street_id = element["ID"]
                return street_id
            
        raise Exception(f"Street {self._street} not found")
    

    def get_location_id(self, street_id):
        """Return ID of first matching location"""

        s = requests.Session()
        params = {"streetId": street_id, "houseNumber": self._hnr}

        r = s.get(f"{self._api_url}/Main/GetLocations", params=params)
        r.raise_for_status()
        r.encoding = "utf-8"

        result = json.loads(r.text)
        if not result:
            raise Exception(f"No locations found for Street ID {street_id} and House number {self._hnr}")

        for element in result:
            if element["StreetId"] == street_id and element["Text"] == str(self._hnr):
                location_id = element["ID"]
                return location_id
                
        raise Exception(f"Location for Street ID {street_id} with House number {self._hnr} not found")
    

    def fetch(self):

        if not (self._uselocation):
            street_id = self.get_street_id()
            self._location = self.get_location_id(street_id)

        now = datetime.now()

        entries = self.fetch_year(now.year)
        if now.month == 12:
            entries += self.fetch_year(now.year + 1)
        return entries


    def fetch_year(self, year):
        s = requests.Session()
        params = {"bmsLocationId": self._location, "year": year}

        r = s.get(f"{self._api_url}/Main/Calender", params=params)
        r.raise_for_status()
        r.encoding = "utf-8"

        entries = []

        dates = self._ics.convert(r.text)
        mapping = ICON_MAP.get(self._municipality, None)

        for d in dates:
            if mapping is not None and d[1] in mapping:
                entries.append(
                    Collection(
                        date=d[0],
                        t=mapping[d[1]]["name"],
                        icon=mapping[d[1]]["icon"],
                    )
                )
            else:
                entries.append(Collection(d[0], d[1]))

        return entries