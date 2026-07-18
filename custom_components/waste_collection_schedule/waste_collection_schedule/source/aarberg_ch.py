import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Aarberg"
DESCRIPTION = "Source for Aarberg, Switzerland."
URL = "https://www.aarberg.ch/"
COUNTRY = "ch"
TEST_CASES = {
    "Aarberg": {"zone": "Aarberg"},
    "Grafenmoos": {"zone": "Grafenmoos"},
    "Leimern": {"zone": "Leimern"},
    "Mülital": {"zone": "Mülital"},
    "Spins": {"zone": "Spins"},
    "Zälgli": {"zone": "Zälgli"},
}

ICON_MAP = {
    "Hauskehricht": Icons.GENERAL_WASTE,
    "Grüngut": Icons.ORGANIC,
    "Papier und Karton": Icons.PAPER,
    "Häckseldienst": Icons.GARDEN,
}

BASE_URL = "https://www.aarberg.ch"
API_URL = f"{BASE_URL}/de/abfallwirtschaft/abfallkalender/"

PARAM_TRANSLATIONS = {
    "en": {
        "zone": "Zone",
    },
    "de": {
        "zone": "Zone",
    },
    "fr": {
        "zone": "Zone",
    },
    "it": {
        "zone": "Zona",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "The zone/area within Aarberg, e.g. Aarberg, Grafenmoos, Leimern, Mülital, Spins, Zälgli",
    },
    "de": {
        "zone": "Die Zone innerhalb von Aarberg, z.B. Aarberg, Grafenmoos, Leimern, Mülital, Spins, Zälgli",
    },
    "fr": {
        "zone": "La zone à Aarberg, par exemple Aarberg, Grafenmoos, Leimern, Mülital, Spins, Zälgli",
    },
    "it": {
        "zone": "La zona ad Aarberg, ad esempio Aarberg, Grafenmoos, Leimern, Mülital, Spins, Zälgli",
    },
}


class Source:
    def __init__(self, zone: str):
        self._zone = zone.strip()

    def fetch(self) -> list[Collection]:
        session = requests.session()

        # get the calendar page to determine the available zones and their ids
        r = session.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        zone_select = soup.find("select", {"id": "zone_id"})
        if zone_select is None:
            raise Exception("No zone_id select found")

        zone_id = None
        zone_names = []
        for option in zone_select.find_all("option"):
            value = option.get("value")
            if not value:
                continue
            name = re.sub(r"\s*\(\d+\)\s*$", "", option.text.strip())
            zone_names.append(name)
            if name.lower() == self._zone.lower():
                zone_id = value

        if zone_id is None:
            raise SourceArgumentNotFoundWithSuggestions("zone", self._zone, zone_names)

        # get the calendar page filtered to the requested zone
        r = session.get(API_URL, params={"zone_id": zone_id})
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

        r = session.get(href)
        r.raise_for_status()

        ics = ICS()
        dates = ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1])))

        return entries
