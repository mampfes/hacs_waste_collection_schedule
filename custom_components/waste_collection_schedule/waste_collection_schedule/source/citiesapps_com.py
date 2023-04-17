from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.CitiesAppsCom import CitiesApps, SERVICE_MAP

from datetime import datetime

EXTRA_INFO = SERVICE_MAP
TITLE = "App CITIES"
DESCRIPTION = "Source for App CITIES."
URL = "https://citiesapps.com"
TEST_CASES = {
    "Fürstenfeld Haushalt Altenmarkt": {
        "city": "Fürstenfeld",
        "calendar": "Haushalt Altenmarkt"
    },
    "Buch - St. Magdalena Buch - St. Magdalena": {
        "city": "Buch - St. Magdalena",
        "calendar": "Buch - St. Magdalena"
    },
    "Rudersdorf Rudersdorf 3": {
        "city": "Rudersdorf",
        "calendar": "Rudersdorf 3"
    },
    "Lieboch": {
        "city": "Lieboch",
        "calendar": "Lieboch"
    }
}
COUNTRY = "at"


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Biomüll": "mdi:leaf",
    "Altpapier": "mdi:package-variant",
    "Papier": "mdi:package-variant",
    "Leichtfraktion": "mdi:recycle",
    "Leichtverpackung": "mdi:recycle",
    "Gelber": "mdi:recycle",
    "Sonder-": "mdi:dump-truck",
    "Abfallwirtschaftszentrum": "mdi:house",
    "Strauchschnitt": "mdi:tree",
    "Metallverpackung": "mdi:can",
}



class Source:
    def __init__(self, city: str, calendar: str):
        self._city: str = city
        self._calendar: str = calendar

    def fetch(self):
        cities_apps = CitiesApps()
        garbage_plans = cities_apps.fetch_garbage_plans(
            self._city, self._calendar)

        entries = []
        for garbage_plan in garbage_plans:
            bin_type = garbage_plan["garbage_type"]["name"]
            icon = ICON_MAP.get(bin_type.split(" ")[0])  # Collection icon

            for date_string in garbage_plan["dates"]:
                date = datetime.strptime(date_string, "%Y-%m-%d").date()
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
