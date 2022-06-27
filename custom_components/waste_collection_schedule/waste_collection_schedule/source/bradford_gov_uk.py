import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import http.client as http_client

TITLE = "Bradford.gov.uk"
DESCRIPTION = "Source for Bradford.gov.uk services for Bradford Metropolitan Council, UK."
URL = "https://onlineforms.bradford.gov.uk/ufs/"
TEST_CASES = {
    "Ilkley":   {"uprn": "100051250665"},
    "Bradford": {"uprn": "100051239296"},
    "Baildon":  {"uprn": "10002329242"},
}

ICONS = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}

from pprint import pprint

class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        entries = []

        s = requests.Session()
        s.cookies.set("COLLECTIONDATES", self._uprn, domain="onlineforms.bradford.gov.uk")
        r = s.get(
          f"{URL}/collectiondates.eb"
        )

        soup = BeautifulSoup(r.text, features="html.parser")
        div = soup.find_all('table', { "role": "region" })
        for region in div:
            displayClass = list(filter (lambda x:x.endswith("-Override-Panel") , region['class']))
            if len(displayClass) > 0:
                heading = region.find_all('td', {"class": displayClass[0].replace('Panel', 'Header')})
                type = "UNKNOWN"
                if "General" in heading[0].text:
                    type = "REFUSE"
                elif "Recycling" in heading[0].text:
                    type = "RECYCLING"
                elif "Garden" in heading[0].text:
                    type = "GARDEN"
                lines = region.find_all('div', { "type": "text" })[0].text
                try:
                  entries.append(
                    Collection(
                        date=datetime.strptime(lines.strip(), "%a %b %d %Y").date(),
                        t=type,
                        icon=ICONS[type],
                       )
                   )
                except ValueError:
                    pass  # ignore date conversion failure for not scheduled collections

        return entries
