from datetime import datetime

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.CitiesAppsCom import SERVICE_MAP, CitiesApps

EXTRA_INFO = SERVICE_MAP
TITLE = "App CITIES"
DESCRIPTION = "Source for App CITIES."
URL = "https://citiesapps.com"
TEST_CASES = {
    "Fürstenfeld Haushalt Altenmarkt": {
        "city": "Fürstenfeld",
        "calendar": "Haushalt Altenmarkt",
        "email": "!secret citiesapps_com_email",
        "phone": "!secret citiesapps_com_phone",
        "password": "!secret citiesapps_com_password",
    },
    "Buch - St. Magdalena Buch - St. Magdalena": {
        "city": "Buch - St. Magdalena",
        "calendar": "Buch - St. Magdalena",
        "email": "!secret citiesapps_com_email",
        "phone": "!secret citiesapps_com_phone",
        "password": "!secret citiesapps_com_password",
    },
    "Rudersdorf Wiesengasse": {
        "city": "Rudersdorf",
        "calendar": "Wiesengasse",
        "email": "!secret citiesapps_com_email",
        "phone": "!secret citiesapps_com_phone",
        "password": "!secret citiesapps_com_password",
    },
    "Lieboch": {
        "city": "Lieboch",
        "calendar": "Lieboch",
        "email": "!secret citiesapps_com_email",
        "phone": "!secret citiesapps_com_phone",
        "password": "!secret citiesapps_com_password",
    },
}
COUNTRY = "at"


ICON_MAP = {
    "Restmüll": Icons.GENERAL_WASTE,
    "Biomüll": Icons.BIO_KITCHEN,
    "Altpapier": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Leichtfraktion": Icons.RECYCLING,
    "Leichtverpackung": Icons.PLASTIC_PACKAGING,
    "Leicht-": Icons.RECYCLING,
    "Gelber": Icons.RECYCLING,
    "Sonder-": Icons.BULKY,
    "Abfallwirtschaftszentrum": Icons.GENERAL_WASTE,
    "Strauchschnitt": Icons.GARDEN,
    "Metallverpackung": Icons.METAL,
}


class Source:
    def __init__(self, city: str, calendar: str, password, email=None, phone=None):
        self._city: str = city
        self._calendar: str = calendar
        self._email: str | None = email
        self._phone: str | None = phone
        self._password: str = password

    def fetch(self):
        cities_apps = CitiesApps(
            email=self._email, phone=self._phone, password=self._password
        )

        garbage_plans = cities_apps.fetch_garbage_plans(self._city, self._calendar)

        if garbage_plans["is_v2"]:
            return self.convert_v2(garbage_plans["data"])
        else:
            return self.convert_v1(garbage_plans["data"])

    def convert_v2(self, garbage_plans):
        entries = []
        for garbage_plan in garbage_plans:
            bin_type = garbage_plan["garbageTypeSettings"]["displayName"]
            icon = ICON_MAP.get(bin_type.split(" ")[0])  # Collection icon

            date = datetime.strptime(
                garbage_plan["date"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).date()
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries

    def convert_v1(self, garbage_plans):
        entries = []
        for garbage_plan in garbage_plans:
            bin_type = garbage_plan["garbage_type"]["name"]
            icon = ICON_MAP.get(bin_type.split(" ")[0])  # Collection icon

            for date_string in garbage_plan["dates"]:
                date = datetime.strptime(date_string, "%Y-%m-%d").date()
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
