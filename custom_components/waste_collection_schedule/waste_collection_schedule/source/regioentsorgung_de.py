from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "RegioEntsorgung Städteregion Aachen"
DESCRIPTION = "RegioEntsorgung Städteregion Aachen"
URL = "https://regioentsorgung.de"
TEST_CASES = {
    "Merzbrück": {"city": "Würselen", "street": "Merzbrück", "house_number": 200},
}

API_URL = "https://tonnen.regioentsorgung.de/WasteManagementRegioentsorgung/WasteManagementServlet"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)",
}


class Source:
    def __init__(self, city, street, house_number):
        self.city = city
        self.street = street
        self.house_number = house_number
        self._ics = ICS()

    def fetch(self):
        now = datetime.now()
        year = now.year
        entries = self.get_collection(year)
        if now.month == 12:
            entries += self.get_collection(year + 1)
        return entries

    def get_collection(self, year):
        # Use a session to keep cookies
        session = requests.Session()

        payload = {
            "SubmitAction": "wasteDisposalServices",
        }
        r = session.get(API_URL, headers=HEADERS, params=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "CITYCHANGED",
            "Ort": self.city,
            "Strasse": "",
            "Hausnummer": "",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "STREETCHANGED",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": "",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.CheckAbfuhrtermineModel",
            "SubmitAction": "forward",
            "Ort": self.city,
            "Strasse": self.street,
            "Hausnummer": self.house_number,
            "Zeitraum": f"Jahresübersicht {year}",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.AbfuhrTerminModel",
            "SubmitAction": "forward",
        }
        r = session.post(API_URL, headers=HEADERS, data=payload)
        r.raise_for_status()

        payload = {
            "ApplicationName": "com.athos.kd.regioentsorgung.AbfuhrTerminDownloadModel",
            "ContainerGewaehlt_1": "on",
            "ContainerGewaehlt_2": "on",
            "ContainerGewaehlt_3": "on",
            "ContainerGewaehlt_4": "on",
            "ContainerGewaehlt_5": "on",
            "ContainerGewaehlt_6": "on",
            "ContainerGewaehlt_7": "on",
            "ContainerGewaehlt_8": "on",
            "ContainerGewaehlt_9": "on",
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
            entries.append(Collection(d[0], d[1]))
        return entries
