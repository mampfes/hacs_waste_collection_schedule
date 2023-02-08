from datetime import datetime
from datetime import timedelta
import logging
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import requests
from bs4 import BeautifulSoup

TITLE = "Schweinfurt"
DESCRIPTION = "Source for Schweinfurth, Germany"
URL = "https://www.schweinfurt.de/leben-freizeit/umwelt/abfallwirtschaft/4427.Aktuelle-Abfuhrtermine-und-Muellkalender.html"
TEST_CASES = {
  "TestcaseI": {"address": "Ahornstrasse"},
  "TestcaseII": {"address": "Ahornstrasse", "showmobile": "True"}
}
_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, address, showmobile=False):
        self._address = address
        self._showmobile = showmobile

    def fetch(self):
      headers = {
          'referer': URL
      }

      s = requests.session()
      r = s.get(URL)
      soup = BeautifulSoup(r.text, "html.parser")

      for tag in soup.find_all("option"):
        if self._address in tag.text:
          #print (tag.text, tag.get('value'))
          now = datetime.now()
          nex = now + timedelta(days=365)
          params = {
            "_func":"evList",
            "_mod":"events",
            "ev[start]":now.strftime("%Y-%m-%d"),
            "ev[end]":nex.strftime("%Y-%m-%d"),
            "ev[addr]":tag.get('value'),
          }

      try:
          params
      except:
          raise Exception("Address not found")
          return[]

      if params:
        r = s.get(URL, params=params, headers=headers)

      data = r.json()

      s.close()

      entries = []
      for entry in data['contents']:
        if "Wertstoffhof" not in data['contents'][entry]['title'] or self._showmobile:
          #print ( data['contents'][entry]['start'], data['contents'][entry]['end'],data['contents'][entry]['title'])
          entries.append(
            Collection( datetime.strptime(data['contents'][entry]['start'], '%Y-%m-%d %H:%M:%S').date(),
                        data['contents'][entry]['title']
            )
          )
      return entries