import re
import urllib

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH"
DESCRIPTION = "Source for AWIGO Abfallwirtschaft Landkreis Osnabrück GmbH."
URL = "https://www.awigo.de/"
TEST_CASES = {
    "Bippen Am Bad 4": {"ort": "Bippen", "strasse": "Am Bad", "hnr": 4},
    "fürstenau, Am Gültum, 9": {"ort": "Fürstenau", "strasse": "Am Gültum", "hnr": 9},
    "Melle, Allee, 78-80": {"ort": "Melle", "strasse": "Allee", "hnr": "78-80"},
    "Berge": {"ort": "Berge", "strasse": "Poststr.", "hnr": 3},
}


ICON_MAP = {
    "Restmülltonne": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio-Tonne": "mdi:leaf",
    "Papiermülltonne": "mdi:package-variant",
    "Gelbe Tonne/Gelben Sack": "mdi:recycle",
}


API_URL = "https://www.awigo.de/index.php"


def compare_cities(a: str, b: str) -> bool:
    return (
        re.sub(r"\([0-9]+\)", "", a.lower()).strip()
        == re.sub(r"\([0-9]+\)", "", b.lower()).strip()
    )


class Source:
    def __init__(self, ort: str, strasse: str, hnr: str | int):
        self._ort: str = str(ort)
        self._strasse: str = strasse
        self._hnr: str = str(hnr)
        self._ics = ICS()

    def fetch(self):
        entries = []
        waste_types = ["rest", "paper", "yellow", "brown", "mobile"]

        for active_type in waste_types:
            s = requests.Session()
            args = {
                "legacy_eID": "awigoCalendar",
                "calendar[method]": "getCities",
            }

            for wt in waste_types:
                args[f"calendar[{wt}]"] = 1 if wt == active_type else 0

            r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))

            r.raise_for_status()

            soup = BeautifulSoup(r.text, features="html.parser")
            for option in soup.findAll("option"):
                if compare_cities(self._ort, option.text):
                    args["calendar[cityID]"] = option.get("value")
                    break
            if "calendar[cityID]" not in args:
                raise SourceArgumentNotFoundWithSuggestions(
                    "ort", self._ort, [option.text for option in soup.findAll("option")]
                )

            args["calendar[method]"] = "getStreets"

            r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))
            r.raise_for_status()

            soup = BeautifulSoup(r.text, features="html.parser")
            for option in soup.findAll("option"):
                if option.text.lower().strip() == self._strasse.lower().strip():
                    args["calendar[streetID]"] = option.get("value")
                    break
            if "calendar[streetID]" not in args:
                raise SourceArgumentNotFoundWithSuggestions(
                    "strasse",
                    self._strasse,
                    [option.text for option in soup.findAll("option")]
                )

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
                raise SourceArgumentNotFoundWithSuggestions(
                    "hnr", self._hnr, [option.text for option in soup.findAll("option")]
                )

            args["calendar[method]"] = "getICSfile"
            r = s.post(API_URL, params=urllib.parse.urlencode(args, safe="[]"))
            r = s.get(r.text)
            r.encoding = "utf-8"

            dates = self._ics.convert(r.text)
            for d in dates:
                bin_type = d[1].replace("wird abgeholt.", "").strip()
                entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
