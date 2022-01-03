import datetime
import urllib
import logging
from typing import Dict

import requests
from bs4 import BeautifulSoup
from requests.sessions import dispatch_hook
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "EGN Abfallkalender"
DESCRIPTION = "Source for EGN Abfallkalender"
URL = "https://www.egn-abfallkalender.de/kalender"
TEST_CASES: Dict[str, Dict[str, str]] = {
    "Grevenbroich": {"city": "Grevenbroich" , "district": "Noithausen", "street": "Von-Immelhausen-Straße", 
        "housenumber": "12", "days": 7},
    "Dormagen": {"city": "Dormagen" , "district": "Hackenbroich", "street": "Aggerstraße", 
        "housenumber": "2", "days": 20},
    "Grefrath": {"city": "Grefrath" , "district": "Grefrath", "street": "An Haus Bruch", 
        "housenumber": "18", "days": 8}
    
}

HEADERS = {
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-requested-with": "XMLHttpRequest",
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, city, district, street, housenumber, days=20):
        self._days = days
        self._city = city
        self._district = district
        self._street = street
        self._housenumber = housenumber
        self._iconMap = {
            "grau": "mdi:trash-can",
            "gelb": "mdi:sack",
            "blau": "mdi:package-variant",
            "braun": "mdi:leaf"
        }

    def fetch(self):
        now = datetime.datetime.now().date()
        goal_date = now + datetime.timedelta(days=self._days)
        entries = []

        s = requests.session()
        r = s.get(URL)

        soup = BeautifulSoup(r.text, features="html.parser")
        tag = soup.find("meta", {"name": "csrf-token"})
        if tag == None:
            return []
        HEADERS["x-csrf-token"] = tag["content"]

        post_data = urllib.parse.urlencode({"city": self._city, "district": self._district,
            "street": self._street, "street_number": self._housenumber})
        r = s.post(URL, data=post_data, headers=HEADERS)
        data = r.json()
        if "error" in data and data["error"] == True:
            for type, errormsg in data["errors"].items():
                _LOGGER.error(f"{type} - {errormsg}")
            return []
        

        for year, months in data["waste_discharge"].items():
            for month, days in months.items():
                for day, types in days.items():
                    date = datetime.datetime(year=int(year), month=int(month), day=int(day)).date()
                    if date > goal_date:
                        break
                    for type in types:
                        color = data["trash_type_colors"][str(type).lower()] if data["trash_type_colors"][str(type).lower()] != None else f"Unkown ({type})"
                        icon = self._iconMap[color] if color in self._iconMap else None
                        color = color.capitalize()
                        entries.append(
                            Collection(
                                date, color, icon=icon
                            )
                        )
                else:
                    continue
                break
            else:
                continue
            break

        return entries
