from difflib import get_close_matches

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Ostprignitz-Ruppin"
DESCRIPTION = "Source for Ostprignitz-Ruppin waste collection."
URL = "https://www.ostprignitz-ruppin.de"
COUNTRY = "de"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://www.ostprignitz-ruppin.de/Verwaltung/Dezernate/Dezernat-Bauen-Ordnung-und-Umwelt/Bau-und-Umweltamt/Abfallwirtschaft-M%C3%BCllentsorgung/.\nSelect your municipality (Ort).\nSelect your street (Straße).\nUse the municipality name as the `location` parameter.\nUse the street name as the `street` parameter.",
    "de": "Öffnen Sie https://www.ostprignitz-ruppin.de/Verwaltung/Dezernate/Dezernat-Bauen-Ordnung-und-Umwelt/Bau-und-Umweltamt/Abfallwirtschaft-M%C3%BCllentsorgung/.\nWählen Sie Ihren Ort aus.\nWählen Sie Ihre Straße aus.\nVerwenden Sie den Ortsnamen als Parameter `location`.\nVerwenden Sie den Straßennamen als Parameter `street`.",
}

TEST_CASES = {
    "Am alten Gymnasium 9, 16816 Neuruppin": {
        "location": "Neuruppin",
        "street": "Am alten Gymnasium 9, 16816",
    }
}

MAIN_PAGE = (
    "https://www.ostprignitz-ruppin.de/"
    "Verwaltung/Dezernate/"
    "Dezernat-Bauen-Ordnung-und-Umwelt/"
    "Bau-und-Umweltamt/"
    "Abfallwirtschaft-M%C3%BCllentsorgung/"
)

AUTOCOMPLETE_URL = "https://www.ostprignitz-ruppin.de/output/autocomplete.php"

session = requests.Session()

PARAM_TRANSLATIONS = {
    "de": {
        "location": "Ort",
        "street": "Straße",
    }
}


class Source:
    def __init__(self, location: str, street: str):
        self._location = location
        self._street = street
        self._ics = ICS()

    def _get_locations(self):
        form_url = (
            "https://www.ostprignitz-ruppin.de/"
            "Verwaltung/Dezernate/"
            "Dezernat-Bauen-Ordnung-und-Umwelt/"
            "Bau-und-Umweltamt/"
            "Abfallwirtschaft-M%C3%BCllentsorgung/index.php"
        )

        r = session.get(
            form_url,
            params={
                "ModID": "48",
                "object": "tx,3039.2455.1",
                "La": "1",
                "NavID": "3039.138",
                "kuo": "1",
            },
            timeout=30,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")

        select = soup.find("select", id="sf_locid")

        if select is None:
            raise ValueError("Could not find location dropdown")

        locations = {}

        for option in select.find_all("option"):
            locid = option.get("value", "").strip()
            name = option.get_text(strip=True)

            if locid.startswith("3033."):
                locations[name] = locid

        return locations

    def _get_locid(self):
        locations = self._get_locations()

        for name, locid in locations.items():
            if self._location.lower() in name.lower():
                return locid

        match = get_close_matches(
            self._location,
            locations.keys(),
            n=1,
            cutoff=0.4,
        )

        if not match:
            raise SourceArgumentNotFoundWithSuggestions(
                "location", self._location, list(locations.keys())
            )

        return locations[match[0]]

    def _get_pois(self, locid):
        r = session.get(
            AUTOCOMPLETE_URL,
            params={
                "out": "json",
                "type": "abto",
                "mode": "",
                "select": "2",
                "refid": locid,
                "term": "",
            },
            headers={
                "Referer": MAIN_PAGE,
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        streets = {street_name: pois for pois, street_name in data}

        match = get_close_matches(
            self._street,
            streets.keys(),
            n=1,
            cutoff=0.4,
        )

        if not match:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, list(streets.keys())
            )

        return streets[match[0]]

    def _build_ics_url(self):
        locid = self._get_locid()
        pois = self._get_pois(locid)

        return (
            "https://www.ostprignitz-ruppin.de/output/options.php"
            f"?ModID=48&call=ical&pois={pois}"
            "&monat="
            "&alarm=0"
        )

    def fetch(self):
        url = self._build_ics_url()

        r = session.get(url, timeout=30)
        r.raise_for_status()
        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))

        return entries
