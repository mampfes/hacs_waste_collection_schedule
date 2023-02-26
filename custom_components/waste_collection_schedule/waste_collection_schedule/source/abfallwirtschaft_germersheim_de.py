import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Germersheim"
DESCRIPTION = "Source für Abfallkalender Kreis Germersheim"
URL = "https://www.abfallwirtschaft-germersheim.de"
TEST_CASES = {
    "Bellheim": {"city": "Bellheim", "street": "Albert-Schweitzer-Str."},
    "Hatzenbuehl": {"city": "Hatzenbühl"},
    "hoerdt": {"city": "Hördt", "street": ""},
}

API_URL = "https://www.abfallwirtschaft-germersheim.de/online-service/abfall-termine/abfalltermine-ics-export-bis-240-liter.html"


class Source:
    def __init__(self, city, street=""):
        self._street = street
        self._city = city
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        params = {
            "icsortschaft": self._city,
            "icsabfallart[]": [],
        }

        if self._street != "":
            params["icsstrasse"] = self._street

        r = s.get(API_URL, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        ics_download = soup.find(
            "input", {"type": "hidden", "name": "ICS_DOWNLOAD"}
        ).get("value")
        request_token = soup.find(
            "input", {"type": "hidden", "name": "REQUEST_TOKEN"}
        ).get("value")

        checkbox_class = re.compile("id_form_icsabfallart_[0-9][0-9]?")
        waste_types = soup.find("div", {"class": "ctlg_form_field checkbox"}).find_all(
            "label",
            {
                "for": checkbox_class,
            },
        )
        for waste_type in waste_types:
            params["icsabfallart[]"].append(waste_type.text)

        r = s.post(
            API_URL,
            params=params,
            data={"ICS_DOWNLOAD": ics_download, "REQUEST_TOKEN": request_token},
        )
        r.raise_for_status()

        entries = []

        dates = self._ics.convert(r.text)
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
