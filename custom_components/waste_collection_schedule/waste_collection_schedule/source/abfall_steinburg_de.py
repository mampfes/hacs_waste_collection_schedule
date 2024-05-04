import datetime
import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.service.ICS import ICS

TITLE = "Kreis Steinburg"
DESCRIPTION = "Source script for abfall.steinburg.de"
URL = "https://abfall.steinburg.de"
TEST_CASES = {
    "Wacken": {"city": "Wacken", "street": "Hauptstr.", "street_number": "1"},
    "Vaale": {"city": "Vaale", "street": "Bollweg", "street_number": "1"},
    "Mehlbek": {"city": "Mehlbek", "street": "Dorfstr."},
}

API_URL = "https://abfall.steinburg.de/api_v2/"
ICON_MAP = {
    "Restabfall(14-täglich)": "mdi:trash-can",
    "Restabfall(4-wöchentlich)": "mdi:trash-can",
    "Restabfall(wöchentlich)": "mdi:trash-can",
    "Gelber Sack(14-täglich)": "mdi:recycle",
    "Weihnachtsbaum": "mdi:pine-tree",
    "Bioabfall(14-täglich)": "mdi:leaf",
    "Papiertonne(monatlich)": "mdi:newspaper-variant-multiple-outline",
}


class Source:
    def __init__(self, city: str, street: str, street_number: str | None = None):
        self._city = city
        self._street = street
        self._street_number = street_number if street_number is not None else "0"
        self._ics = ICS()

    def _fetch_data(self, url):
        response = requests.get(url)
        response.encoding = "UTF-8"
        response.raise_for_status()
        return response.json()

    def fetch(self):
        cities_data = self._fetch_data(f"{API_URL}/collection_dates/1/orte")
        selected_city = next(
            (city for city in cities_data["orte"] if city["ortsbezeichnung"].lower() == self._city.lower()), None)
        if selected_city is None:
            raise Exception(
                "No city found that matches the given search parameters. "
                "Please check https://abfall.steinburg.de for cities (without zip code)"
            )

        streets_data = self._fetch_data(f"{API_URL}/collection_dates/1/ort/{selected_city['ortsnummer']}/strassen")
        selected_street = next(
            (street for street in streets_data["strassen"] if
             street["strassenbezeichnung"].lower() == self._street.lower()), None)
        if selected_street is None:
            raise Exception(
                "No street found that matches the given search parameters. "
                "Please check https://abfall.steinburg.de for possible streets."
            )

        waste_type_data = self._fetch_data(
            f"{API_URL}/collection_dates/1/ort/{selected_city['ortsnummer']}/abfallarten")
        waste_types = [waste_type["id"] for waste_type in waste_type_data["abfallarten"]]

        entries_url = (
            f"{API_URL}/collection_dates/1/ort/{selected_city['ortsnummer']}/strasse/"
            f"{selected_street['strassennummer']}/hausnummern/{self._street_number}/abfallarten/"
            f"{'-'.join(waste_types)}/kalender.ics"
        )

        er = requests.get(entries_url)
        er.encoding = "UTF-8"
        er.raise_for_status()
        dates = self._ics.convert(er.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], icon=ICON_MAP.get(d[1])))
        return entries
