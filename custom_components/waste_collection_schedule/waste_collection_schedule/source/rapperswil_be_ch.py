import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Rapperswil"
DESCRIPTION = "Source for Rapperswil."
URL = "https://www.rapperswil-be.ch/"
TEST_CASES: dict[str, dict[str, str]] = {
    "Rapperswil": {},
}


ICON_MAP = {
    "Hauskehricht": "mdi:trash-can",
    "Grüngut": "mdi:leaf",
    "Papier und Karton": "mdi:package-variant",
}

BASE_URL = "https://www.rapperswil-be.ch"
API_URL = f"{BASE_URL}/de/abfallwirtschaft/abfallkalender/"


class Source:
    def __init__(self):
        self._ics = ICS()

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        ical_div = soup.select_one("div#icalTermine")
        if ical_div is None:
            raise Exception("No icalTermine found")
        ical_link_a = ical_div.select_one("a")
        if ical_link_a is None:
            raise Exception("No ical link found")

        href = ical_link_a["href"]
        if not isinstance(href, str):
            raise Exception("No href found")

        if href.startswith("/"):
            href = BASE_URL + href
        if not href.startswith("http"):
            href = API_URL + href

        r = requests.get(href)

        dates = self._ics.convert(r.text.replace("X-WR-TIMEZONE','EUROPE/BERLIN:", ""))
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1])))

        return entries
