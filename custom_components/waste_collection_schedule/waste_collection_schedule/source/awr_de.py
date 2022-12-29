import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Abfallwirtschaft Rendsburg"
DESCRIPTION = "Source for Abfallwirtschaft Rendsburg"
URL = "https://www.awr.de"
TEST_CASES = {
    "Rendsburg": {"city": "Rendsburg", "street": "Hindenburgstraße"},
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, city, street):
        self._city = city
        self._street = street
        self._ics = ICS()

    def fetch(self):
        # retrieve list of cities
        r = requests.get("https://www.awr.de/api_v2/collection_dates/1/orte")
        r.raise_for_status()
        cities = r.json()

        # create city to id map from retrieved cities
        city_to_id = {
            city["ortsbezeichnung"]: city["ortsnummer"] for (city) in cities["orte"]
        }

        if self._city not in city_to_id:
            raise Exception(f"city not found: {self._city}")

        cityId = city_to_id[self._city]

        # retrieve list of streets
        r = requests.get(
            f"https://www.awr.de/api_v2/collection_dates/1/ort/{cityId}/strassen"
        )
        r.raise_for_status()
        streets = r.json()

        # create street to id map from retrieved cities
        street_to_id = {
            street["strassenbezeichnung"]: street["strassennummer"]
            for (street) in streets["strassen"]
        }

        if self._street not in street_to_id:
            raise Exception(f"street not found: {self._street}")

        streetId = street_to_id[self._street]

        # retrieve list of waste types
        r = requests.get(
            f"https://www.awr.de/api_v2/collection_dates/1/ort/{cityId}/abfallarten"
        )
        r.raise_for_status()
        waste_types = r.json()
        wt = "-".join([t["id"] for t in waste_types["abfallarten"]])

        # get ics file
        r = requests.get(
            f"https://www.awr.de/api_v2/collection_dates/1/ort/{cityId}/strasse/{streetId}/hausnummern/0/abfallarten/{wt}/kalender.ics"
        )

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1]))
        return entries
