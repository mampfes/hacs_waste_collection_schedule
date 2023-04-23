import datetime
import json
import logging
import xml.etree.ElementTree

import requests
from waste_collection_schedule import Collection

TITLE = "Poznań/Koziegłowy/Objezierze/Oborniki"
DESCRIPTION = "Source for Poznań/Koziegłowy/Objezierze/Oborniki city garbage collection"
URL = "https://sepan.remondis.pl"
TEST_CASES = {
    "Street Name": {
        "city": "Poznań",
        "street_name": "ŚWIĘTY MARCIN",
        "street_number": "1",
    },
}

_LOGGER = logging.getLogger(__name__)


API_URL = "https://sepan.remondis.pl/harmonogram"

NAME_MAP = {
    1: "Zmieszane odpady komunalne",
    2: "Papier",
    3: "Metale i tworzywa sztuczne",
    4: "Szkło",
    5: "Bioodpady",
    6: "Drzewka świąteczne",
    7: "Odpady wystawkowe",
}

ICON_MAP = {
    1: "mdi:trash-can",
    2: "mdi:recycle",
    3: "mdi:recycle",
    4: "mdi:recycle",
    5: "mdi:recycle",
    6: "mdi:recycle",
    7: "mdi:trash-can",
}


class Source:
    def __init__(self, city, street_name, street_number):
        self._city = city.upper()
        self._street_name = street_name.upper()
        self._street_number = street_number.upper()

    def fetch(self):
        r = requests.get(f"{API_URL}/addresses/cities")
        r.raise_for_status()
        city_id = 0
        cities = json.loads(r.text)
        for item in cities:
            if item["value"] == self._city:
                city_id = item["id"]
        if city_id == 0:
            raise Exception("city not found")

        r = requests.get(f"{API_URL}/addresses/streets/{city_id}")
        r.raise_for_status()
        street_id = 0
        streets = json.loads(r.text)
        for item in streets:
            if item["value"] == self._street_name:
                street_id = item["id"]
        if street_id == 0:
            raise Exception("street not found")

        r = requests.get(f"{API_URL}/addresses/numbers/{city_id}/{street_id}")
        r.raise_for_status()
        number_id = 0
        numbers = json.loads(r.text)
        for item in numbers:
            if item["value"] == self._street_number:
                number_id = item["id"]
        if number_id == 0:
            raise Exception("number not found")

        r = requests.get(f"{API_URL}/reports?type=html&id={number_id}")
        r.raise_for_status()
        report = json.loads(r.text)
        if report["status"] != "success":
            raise Exception("fetch report failed")

        r = requests.get(report["filePath"])
        r.raise_for_status()
        table = r.text[r.text.find("<table") : r.text.rfind("</table>") + 8]
        tree = xml.etree.ElementTree.fromstring(table)
        year = datetime.date.today().year

        entries = []
        for row_index, row in enumerate(tree.findall(".//tr")):
            if row_index > 0:
                for cell_index, cell in enumerate(row.findall(".//td")):
                    if cell_index > 0 and isinstance(cell.text, str):
                        for day in cell.text.split(","):
                            entries.append(
                                Collection(
                                    datetime.date(year, row_index - 1, int(day)),
                                    NAME_MAP[cell_index],
                                    ICON_MAP[cell_index],
                                )
                            )

        return entries
