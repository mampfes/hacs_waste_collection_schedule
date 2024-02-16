import csv
from datetime import datetime, timedelta

import requests

from ..collection import Collection

TITLE = "Rudna u Prahy"
DESCRIPTION = "Source for Rudna u Prahy waste collection"
URL = "https://www.rudnamesto.cz/"
COUNTRY = "cz"
TEST_CASES = {
    "North part of the city": {"city_part": "S"},
    "South part of the city": {"city_part": "J"},
    "ALL": {"city_part": ""},
}

WASTE_TYPES_URL = "https://mesto-rudna.cz/odpadovy-kalendar/data_description.csv"
WASTE_DATES_URL = "https://mesto-rudna.cz/odpadovy-kalendar/data_calendar.csv"

ICON_MAP = {
    "B": "mdi:compost",
    "TKOS": "mdi:trash-can",
    "TKOJ": "mdi:trash-can",
    "PET": "mdi:recycle",
    "BS": "mdi:pine-tree",
    "SHK": "mdi:pot",
    "SHPA": "mdi:note-text-outline",
    "SHPL": "mdi:recycle-variant",
    "SHS": "mdi:glass-fragile",
    "NO": "mdi:skull-scan",
}

class Source:
    def __init__(self, city_part=''):
        self._city_part = city_part

    def fetch(self):
        session = requests.Session()

        csv_content = session.get(WASTE_TYPES_URL).content.decode("utf-8")

        csv_lines = list(csv.reader(csv_content.splitlines(), delimiter=";"))

        waste_types = {}

        for row in csv_lines:
          mydict = {'desc':row[1],'icon':ICON_MAP.get(row[0])}
          waste_types[row[0]] = mydict


        csv_content = session.get(WASTE_DATES_URL).content.decode("utf-8")

        csv_lines = list(csv.reader(csv_content.splitlines(), delimiter=";"))

        entries = []

        format = "%Y-%m-%d"

        for row in csv_lines:
          if self._city_part.lower() == 's':
            if row[2] == "TKOJ":
              continue
          if self._city_part.lower() == 'j':
            if row[2] == "TKOS":
              continue
          pickup_date = datetime.strptime(row[1], format)
          waste_type = waste_types[row[2]]['desc']
          icon = waste_types[row[2]]['icon']
          pic = ''
        

          entries.append(
            Collection(pickup_date.date(), waste_type, picture=pic, icon=icon)
          )

        return entries
