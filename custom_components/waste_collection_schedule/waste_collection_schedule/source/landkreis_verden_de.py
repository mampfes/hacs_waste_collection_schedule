from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Verden"
DESCRIPTION = "Source for Landkreis Verden waste collection."
URL = "https://www.landkreis-verden.de/"
TEST_CASES = {
    "Achim": {"city": "Achim", "street": "Am Schießstand", "house_number": 10},
    "Blender": {
        "city": "Blender",
        "street": "Buchenweg",
        "house_number": "8",
        "house_number_addition": "a",
    },
    "Riede": {"city": "Riede", "street": "An der Reihe", "house_number": 11},
}

API_URL = "https://lkv.landkreis-verden.de/WasteManagementVerden/WasteManagementServlet"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
}

ICON_MAP = {
    "Gelber": "mdi:recycle",
    "Restabfallbehaelter": "mdi:trash-can",
    "Papierbehaelter": "mdi:newspaper",
    "Kompostbehaelter": "mdi:leaf",
    "Weihnachtsbaum": "mdi:pine-tree",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "street": "Straße",
        "house_number": "Hausnummer",
        "house_number_addition": "Hausnummerzusatz",
    },
}


class Source:
    def __init__(
        self,
        city: str,
        street: str,
        house_number: int | str,
        house_number_addition: str | None = None,
    ) -> None:
        self.city: str = city
        self.street: str = street
        self.house_number: str | int = house_number
        self.house_number_addition: str = (
            house_number_addition if house_number_addition else ""
        )
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        now = datetime.now()
        year = now.year
        entries = self.get_collection(year)
        if now.month == 12:
            entries += self.get_collection(year + 1)
        return entries

    def get_collection(self, year: int) -> list[Collection]:
        # Use a session to keep cookies
        session = requests.Session()

        payload: dict[str, str | int] = {
            "SubmitAction": "wasteDisposalServices",
            "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
        }
        r = session.get(API_URL, headers=HEADERS, params=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.nl.mvc.abfterm.CheckAbfuhrTermineParameterBusinessCase",
            "SubmitAction": "CITYCHANGED",
            "Ort": self.city,
            "Strasse": "",
            "Hausnummer": "",
            "Hausnummerzusatz": "",
            "Zeitraum": f"Jahresübersicht {year}",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.nl.mvc.abfterm.CheckAbfuhrTermineParameterBusinessCase",
            "SubmitAction": "STREETCHANGED",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": "",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.nl.mvc.abfterm.CheckAbfuhrTermineParameterBusinessCase",
            "ContainerGewaehltR": "on",
            "ContainerGewaehlt4": "on",
            "ContainerGewaehltK": "on",
            "ContainerGewaehltP": "on",
            "ContainerGewaehltG": "on",
            "ContainerGewaehltW": "on",
            "ContainerGewaehltB": "on",
            "SubmitAction": "forward",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": self.house_number,
            "Hausnummerzusatz": self.house_number_addition,
            "Zeitraum": f"Jahresübersicht {year}",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)

        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.nl.mvc.abfterm.CheckAbfuhrTermineParameterBusinessCase",
            "ContainerGewaehltR": "on",
            "ContainerGewaehlt4": "on",
            "ContainerGewaehltK": "on",
            "ContainerGewaehltP": "on",
            "ContainerGewaehltG": "on",
            "ContainerGewaehltW": "on",
            "ContainerGewaehltB": "on",
            "SubmitAction": "forward",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummernwahl": str(self.house_number) + self.house_number_addition,
            "Zeitraum": f"Jahresübersicht {year}",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.nl.mvc.abfterm.AbfuhrTerminModel",
            "ContainerGewaehltR": "on",
            "ContainerGewaehlt4": "on",
            "ContainerGewaehltK": "on",
            "ContainerGewaehltP": "on",
            "ContainerGewaehltG": "on",
            "ContainerGewaehltW": "on",
            "ContainerGewaehltB": "on",
            "ICalErinnerung": "keine Erinnerung",
            "ICalZeit": "06:00 Uhr",
            "SubmitAction": "filedownload_ICAL",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        # Parse ics file
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].split()[0])))
        return entries
