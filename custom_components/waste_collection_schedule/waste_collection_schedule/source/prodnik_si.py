import json
from datetime import datetime, timezone

import requests
from waste_collection_schedule import Collection

TITLE = "Prodnik"
DESCRIPTION = "Source for Prodnik."
URL = "https://prodnik.si"
TEST_CASES = {
    "Test1": {
        "customer_number": "!secret prodnik_si_customer_number",
        "password": "!secret prodnik_si_password",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Go to "https://e.prodnik.si/Registracija" to register.'
}

PARAM_DESCRIPTIONS = {
    "en": {
        "customer_number": "Your customer number written on the bill.",
        "password": "Your password created during the registration.",
    }
}

ICON_MAP = {
    "m": "mdi:trash-can",
    "b": "mdi:leaf",
    "e": "mdi:recycle",
    "k": "mdi:dump-truck",
}

BIN_TYPES = {
    "m": "Mesani",
    "b": "Bioloski",
    "e": "Embalaza",
    "k": "Kosovni",
}


LOGIN_URL = "https://e.prodnik.si/Prijava"
BASE_URL = "https://e.prodnik.si/Domov"


class Source:
    def __init__(self, customer_number: str, password: str):
        self._customer_number = customer_number
        self._password = password

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        r = s.get(LOGIN_URL)
        r.raise_for_status()
        html = r.text

        viewstate = self.extract_login(html, '__VIEWSTATE" value="')
        viewstate_gen = self.extract_login(html, '__VIEWSTATEGENERATOR" value="')
        event_validation = self.extract_login(html, '__EVENTVALIDATION" value="')

        data = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_gen,
            "__EVENTVALIDATION": event_validation,
            "ctl00$MainContentPlaceHolder$UcLogin1$ctrLogin$UserName": self._customer_number,
            "ctl00$MainContentPlaceHolder$UcLogin1$ctrLogin$Password": self._password,
            "__EVENTTARGET": "ctl00$MainContentPlaceHolder$UcLogin1$ctrLogin$LoginBtn",
            "__EVENTARGUMENT": "",
        }

        r = s.post(LOGIN_URL, data=data)
        r.raise_for_status()
        if "Uporabniško ime oz. geslo ni pravilno." in r.text:
            raise Exception("Login failed: invalid credentials")

        r = s.get(BASE_URL)
        r.raise_for_status()
        sched_html = r.text

        json_data = self.extract_json_from_html(sched_html)
        collections = json.loads(json_data)

        entries = []
        for collection in collections:
            # Choosing only the sixth char from example: "Odvoz kosovnih odpadkov"
            type_char = collection["Subject"][6]
            if type_char not in BIN_TYPES:
                continue
            bin_type = BIN_TYPES.get(type_char)
            icon = ICON_MAP.get(type_char)
            start_str = collection.get("StartTime", "")
            if start_str.startswith("/Date(") and start_str.endswith(")/"):
                timestamp_str = start_str[len("/Date(") : -len(")/")]
                ts = int(timestamp_str) / 1000
                d = datetime.fromtimestamp(ts, tz=timezone.utc).date()
                entries.append(Collection(date=d, t=bin_type, icon=icon))
        return entries

    def extract_login(self, text: str, marker: str) -> str:
        idx = text.find(marker)
        start = idx + len(marker)
        end = text.find('"', start)
        return text[start:end]

    def extract_json_from_html(self, text: str) -> str:
        marker = 'appointmentSettings":{"dataSource":ej.isJSON('
        start = text.find(marker) + len(marker)
        end = text.find("]", start) + 1
        return text[start:end]
