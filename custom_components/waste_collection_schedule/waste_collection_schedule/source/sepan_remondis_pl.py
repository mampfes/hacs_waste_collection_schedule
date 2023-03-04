import logging
import datetime
import xml.etree.ElementTree

import json
import requests
from waste_collection_schedule import Collection

TITLE = "Poznań/Koziegłowy/Objezierze/Oborniki"
DESCRIPTION = "Source for Poznań/Koziegłowy/Objezierze/Oborniki city garbage collection"
URL = "https://sepan.remondis.pl/harmonogram/"
TEST_CASES = {
    "Street Name": {"city": "Poznań", "street_name": "ŚWIĘTY MARCIN", "street_number": "1"},
}

_LOGGER = logging.getLogger(__name__)


class SourceConfigurationError(ValueError):
    pass


class SourceParseError(ValueError):
    pass


PAGE_URL = "https://sepan.remondis.pl/harmonogram"

NAME_MAP = {
    1: "Zmieszane odpady komunalne",
    2: "Papier",
    3: "Metale i tworzywa sztuczne",
    4: "Szkło",
    5: "Bioodpady",
    6: "Drzewka świąteczne",
    7: "Odpady wystawkowe",
}

class Source:
    def __init__(self, city=None, street_name=None, street_number=None):
        if city is None or street_name is None or street_number is None:
            raise SourceConfigurationError(
                "All params city, street_name and street_number must have a value"
            )
        self._city = city.upper()
        self._street_name = street_name.upper()
        self._street_number = street_number.upper()

    def fetch(self):
        entries = []

        url = f"{PAGE_URL}/addresses/cities"
        r = requests.get(url)
        city_id = 0
        cities = json.loads(r.text)
        for item in cities:
          if item["value"] == self._city:
            city_id = item["id"]
        if city_id == 0:
          _LOGGER.debug(f"No such city")
          return entries

        url = f"{PAGE_URL}/addresses/streets/{city_id}"
        r = requests.get(url)
        street_id = 0
        streets = json.loads(r.text)
        for item in streets:
          if item["value"] == self._street_name:
            street_id = item["id"]
        if street_id == 0:
          _LOGGER.debug(f"No such street")
          return entries
        
        url = f"{PAGE_URL}/addresses/numbers/{city_id}/{street_id}"
        r = requests.get(url)
        number_id = 0
        numbers = json.loads(r.text)
        for item in numbers:
          if item["value"] == self._street_number:
            number_id = item["id"]
        if number_id == 0:
          _LOGGER.debug(f"No such number")
          return entries

        url = f"{PAGE_URL}/reports?type=html&id={number_id}"
        r = requests.get(url)
        report = json.loads(r.text)
        if report["status"] == "success":
          url = report["filePath"]
        if url == "":
          _LOGGER.debug(f"Error fetching report")
          return entries

        r = requests.get(url)
        table = r.text[r.text.find('<table'):r.text.rfind('</table>')+8]
        tree = xml.etree.ElementTree.fromstring(table)
        year = datetime.date.today().year
        for row_index, row in enumerate(tree.findall('.//tr')):
          if row_index > 0:
            cells = row.findall('.//td')
            for cell_index, cell in enumerate(row.findall('.//td')):
              if cell_index > 0 and isinstance(cell.text, str):
                for day in cell.text.split(','):
                  entries.append(Collection(datetime.date(year, row_index-1, int(day)), NAME_MAP[cell_index]))

        return entries
