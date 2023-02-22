from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import json
import requests
from bs4 import BeautifulSoup

TITLE = "City of Onkaparinga Council"
DESCRIPTION = "Source for City of Onkaparinga Council, Australia."
URL = "https://www.onkaparingacity.com/"
COUNTRY = "au"
TEST_CASES = {
    "TestcaseI": {"address": "18 Flagstaff Road, FLAGSTAFF HILL 5159"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling Waste": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}

class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        url = "https://www.onkaparingacity.com/api/v1/myarea/search"

        headers = {
        'referer': 'https://www.onkaparingacity.com/Services/Waste-and-recycling/Bin-collections'
        }

        params = {
        'keywords': self._address
        }

        r = requests.get(url, params=params, headers=headers)

        addresses = r.json()
        
        if addresses == 0:
          return []

        url = 'https://www.onkaparingacity.com/ocapi/Public/myarea/wasteservices'

        params = {
        'geolocationid': addresses['Items'][0]['Id'],
        'ocsvclang': 'en-AU'

        }

        r = requests.get(url, params=params, headers=headers)

        waste = r.json()

        soup = BeautifulSoup(waste['responseContent'], "html.parser")

        waste_type = []

        for tag in soup.find_all("h3"):
            if tag.text.startswith('Calendar'):
                continue
            waste_type.append(tag.text)

        waste_date = []
        for tag in soup.find_all("div", {"class":"next-service"}):
          tag_text = tag.text.strip()
          if tag_text != "":
            date_object = datetime.strptime(tag_text, '%a %d/%m/%Y').date()
            waste_date.append(date_object)

        waste = list(zip(waste_type, waste_date))

        entries = []
        for item in waste:
            icon = ICON_MAP.get(item[0])
            entries.append(
                Collection(item[1], item[0], icon=icon)
            )

        return entries
