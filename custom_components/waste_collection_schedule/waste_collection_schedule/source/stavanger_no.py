from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import json
import requests
from bs4 import BeautifulSoup

TITLE = "Stavanger"
DESCRIPTION = "Source for Stavanger Kommune, Norway"
URL = "https://www.stavanger.kommune.no/"
TEST_CASES = {
    "TestcaseI": {"id": "57bf9d36-722e-400b-ae93-d80f8e354724", "municipality": "Stavanger", "gnumber": "57", "bnumber": "922", "snumber": "0"},
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Papp/papir": "mdi:recycle",
    "Bio": "mdi:leaf",
    "Juletre": "mdi:pine-tree",
}

class Source:
    def __init__(self, id, municipality, gnumber, bnumber, snumber):
        self._id = id
        self._municipality = municipality
        self._gnumber = gnumber
        self._bnumber = bnumber
        self._snumber = snumber

    def fetch(self):
      url = 'https://www.stavanger.kommune.no/renovasjon-og-miljo/tommekalender/finn-kalender/show'
      headers = {
          'referer': 'https://www.stavanger.kommune.no'
      }

      params = {
          'id' : self._id,
          'municipality' : self._municipality,
          'gnumber' : self._gnumber,
          'bnumber' : self._bnumber,
          'snumber' : self._snumber
      }

      r = requests.get(url, params=params, headers=headers)

      print(r.text)

      soup = BeautifulSoup(r.text, "html.parser")

      tag = soup.find_all("option")
      year = tag[0].get('value').split('-')
      year = year[1]

      entries = []
      for tag in soup.find_all("tr", {"class":"waste-calendar__item"}):
        if tag.text.strip() == 'Dato og dag\nAvfallstype':
          continue

        date = tag.text.strip().split(' - ')
        date =  datetime.strptime(date[0]+'.'+year, '%d.%m.%Y').date()
        #print (date)

        for img in tag.find_all("img"):
          print (date,img.get('title'))
          icon = ICON_MAP.get(img.get('title'))
          entries.append(
            Collection(date, img.get('title'), icon=icon)
          )

      return entries
