from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Bremerhavener Entsorgungsgesellschaft mbH"
DESCRIPTION = "Source for Bremerhavener Entsorgungsgesellschaft mbH."
URL = "https://beg-bhv.de"
TEST_CASES = {
    "Hafenstraße 22": {"street": "Hafenstraße, Bremerhaven", "hnr": 2},
    "Hadeler Heide, Cuxhaven": {
        "street": "Hadeler Heide, Cuxhaven",
        "hnr": "2",
        "two_weeks": True,
    },
}


ICON_MAP = {
    "Graue tonne": "mdi:trash-can",
    "Gelber sack": "mdi:recycle",
    "Gelbe tonne" "Tannenbaum": "mdi:pine-tree",
}


API_URL = "https://kalender.beg-logistics.de/schedules/public"
API_URL2 = "https://kalender.beg-logistics.de/sessions"
STREETS_SEARCH_URL = "https://kalender.beg-logistics.de/auto_complete/streets.json"
STREET_UPDATE_URL = "https://kalender.beg-logistics.de/auto_complete/update_street.js"

PARAM_TRANSLATIONS = {
    "de": {
        "street": "Straße",
        "hnr": "Hausnummer",
        "two_weeks": "14-tägliche Abfuhr",
    }
}


class Source:
    def __init__(self, street: str, hnr: str | int, two_weeks: bool = False):
        self._street: str = street
        self._hnr: str | int = hnr
        self._two_weeks: bool = two_weeks

    def fetch_street(self, s: requests.Session, term: str | None = None) -> str:
        args = {"term": term if term is not None else self._street}
        r = s.get(STREETS_SEARCH_URL, params=args)
        r.raise_for_status()
        streets = r.json()
        for street in streets:
            if (
                street.lower().replace(",", "").replace(".", "").casefold()
                == self._street.lower().replace(",", "").replace(".", "").casefold()
            ):
                return street
        if term is None and "," in self._street:
            return self.fetch_street(s, self._street.split(",")[0])
        raise SourceArgumentNotFoundWithSuggestions("street", self._street, streets)

    def fetch(self) -> list[Collection]:
        s = requests.session()
        self._street = self.fetch_street(s)

        r = s.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.select_one("form#new_session")
        if not form:
            raise ValueError("No form found on " + API_URL)
        args = {}
        for input in form.select("input"):
            if "name" in input.attrs and "value" in input.attrs:
                args[input["name"]] = input["value"]
        args["session[street]"] = self._street
        args["session[number]"] = self._hnr
        args["session[two_weeks]"] = ["0", "1" if self._two_weeks else "0"]

        r = s.post(API_URL2, data=args)

        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for li in soup.select("ul.list li.day"):
            date_str = li.get_text(strip=True).split(" ")[-1]
            date = datetime.strptime(date_str, "%d.%m.%Y").date()
            imgs = li.select("img")
            for img in imgs:
                type = img["alt"]
                icon = ICON_MAP.get(type)
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
