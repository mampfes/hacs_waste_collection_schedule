import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "AWG Wuppertal"
DESCRIPTION = "Source for AWG Wuppertal."
URL = "https://awg-wuppertal.de/"
TEST_CASES = {"Hauptstraße": {"street": "Hauptstraße"}}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Gelb": "mdi:recycle",
    "Bio": "mdi:leaf",
    "Papier": "mdi:package-variant",
    "Sperrmüll": "mdi:sofa",
    "Weihnachtsbaumabholung": "mdi:pine-tree",
}

BASE_URL = "https://awg-wuppertal.de"
API_URL = f"{BASE_URL}/privatkunden/abfallkalender.html"


class Source:
    def __init__(self, street: str):
        self._street: str = street
        self._confirmed_street: str | None = None
        self._ics = ICS(
            split_at="/",
            regex=r"(.*)/ !!! Terminverschiebung !!!",
        )

    @staticmethod
    def _search_street(street: str) -> list[str]:
        params = {
            "eID": "wastecalendar_autocomplete",
            "term": street,
        }
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        if not data and len(street) > 3:
            return Source._search_street(street[:-1])
        return data

    def confirm_street(self) -> None:
        streets = Source._search_street(self._street)
        for street in streets:
            if self._street.lower().replace(" ", "") == street.lower().replace(" ", ""):
                self._confirmed_street = street
                return
        raise SourceArgumentNotFoundWithSuggestions("street", self._street, streets)

    def fetch(self) -> list[Collection]:
        if not self._confirmed_street:
            self.confirm_street()
        if not self._confirmed_street:
            raise Exception("Could not confirm street")

        # get json file
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.select_one("form[name='demand']")
        if not form:
            raise Exception("Could not find form element on initial page")

        action = form["action"]
        if not isinstance(action, str):
            raise Exception("Could not find form action")
        if action.startswith("/"):
            action = BASE_URL + action
        data = {}
        for input in form.select("input"):
            if "name" not in input.attrs or "value" not in input.attrs:
                continue
            data[input["name"]] = input["value"]
        data["tx_bwwastecalendar_pi1[demand][streetname]"] = self._confirmed_street

        r = requests.post(action, data=data)
        soup = BeautifulSoup(r.text, "html.parser")

        # get all links where text ends on "als iCal"
        ical_links = soup.find_all(
            "a", text=lambda text: text and text.lower().strip().endswith("als ical")
        )
        entries = []
        for link in ical_links:
            href = link["href"]
            if href.startswith("/"):
                href = BASE_URL + href
            r = requests.get(href)
            r.raise_for_status()
            events = self._ics.convert(r.text)
            for date_, name in events:
                icon = ICON_MAP.get(name.split("-")[0])
                entries.append(Collection(date=date_, t=name, icon=icon))
        return entries
