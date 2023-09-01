import urllib

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH"
DESCRIPTION = "Source for AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH."
URL = "https://www.awigo.de/"
TEST_CASES = {
    "Bippen Am Bad 4": {"ort": "Bippen", "strasse": "Am Bad", "hnr": 4},
    "fürstenau, Am Gültum, 9": {"ort": "Fürstenau", "strasse": "Am Gültum", "hnr": 9},
    "Melle, Allee, 78-80": {"ort": "Melle", "strasse": "Allee", "hnr": "78-80"},
}


ICON_MAP = {
    "Restmülltonne": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio-Tonne": "mdi:leaf",
    "Papiermülltonne": "mdi:package-variant",
    "Gelbe Tonne/Gelben Sack": "mdi:recycle",
}


API_URL = "https://www.awigo.de/index.php"


class Source:
    def __init__(self, ort: str, strasse: str, hnr: str | int):
        self._ort: str = str(ort)
        self._strasse: str = strasse
        self._hnr: str = str(hnr)
        self._ics = ICS()

    def fetch(self):
        s = requests.Session()
        args = {
            "eID": "awigoCalendar",
            "calendar[method]": "getCities",
            "calendar[rest]": 1,
            "calendar[paper]": 1,
            "calendar[yellow]": 1,
            "calendar[brown]": 1,
            "calendar[mobile]": 1,
        }

        r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))

        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        for option in soup.findAll("option"):
            if self._ort.lower().strip() in option.text.lower().strip():
                args["calendar[cityID]"] = option.get("value")
                break
        if "calendar[cityID]" not in args:
            raise ValueError(f'City "{self._ort}" not found')

        args["calendar[method]"] = "getStreets"

        r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        for option in soup.findAll("option"):
            if option.text.lower().strip() == self._strasse.lower().strip():
                args["calendar[streetID]"] = option.get("value")
                break
        if "calendar[streetID]" not in args:
            raise ValueError(f'Street "{self._strasse}" not found')

        args["calendar[method]"] = "getNumbers"
        r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))
        soup = BeautifulSoup(r.text, features="html.parser")
        for option in soup.findAll("option"):
            if option.text.lower().strip().replace(
                " ", ""
            ) == self._hnr.lower().strip().replace(" ", ""):
                args["calendar[locationID]"] = option.get("value")
                break
        if "calendar[locationID]" not in args:
            raise ValueError(f'House number "{self._hnr}" not found')

        args["calendar[method]"] = "getICSfile"
        r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))
        r = s.get(r.text)

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            bin_type = d[1].replace("wird abgeholt.", "").strip()
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
