import re
import base64
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Buckinghamshire Waste Collection - Former Chiltern, South Bucks or Wycombe areas"
DESCRIPTION = "Source for chiltern.gov.uk services for parts of Buckinghamshire"
URL = "https://chiltern.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "200000811701"},
    "Test_002": {"uprn": "100080550517"},
    "Test_003": {"uprn": "100081091932"},
    "Test_004": {"uprn": 10094593823},
}

ICON_MAP = {
    "Domestic Refuse Collection": "mdi:trash-can",
    "Domestic Food Collection": "mdi:food",
    "Domestic Garden Collection": "mdi:leaf",
    "Domestic Paper/Card Collection": "mdi:newspaper",
    "Domestic Mixed Dry Recycling Collection": "mdi:glass-fragile",
    "Communal Paper/Card Collection": "mdi:newspaper",
    "Communal Mixed Dry Recycling Collection": "mdi:glass-fragile",
    "Communal Refuse Collection": "mdi:trash-can",
}

class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        # Start a session
        r = session.get("https://chiltern.gov.uk/collection-dates")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url
        form = soup.find("form", attrs={"id": "COPYOFECHOCOLLECTIONDATES_FORM"})
        form_url = form["action"]

        # Submit form
        form_data = {
            "COPYOFECHOCOLLECTIONDATES_FORMACTION_NEXT": "COPYOFECHOCOLLECTIONDATES_ADDRESSSELECTION_NAV1",
            "COPYOFECHOCOLLECTIONDATES_ADDRESSSELECTION_SELECTEDADDRESS": "dummy serverside validaiton only",
            "COPYOFECHOCOLLECTIONDATES_ADDRESSSELECTION_UPRN": self._uprn,
        }
        r = session.post(form_url, data=form_data)
        r.raise_for_status()

        # Extract collection dates
        pattern = r'var COPYOFECHOCOLLECTIONDATES_PAGE1_DATES2Data = JSON.parse\(helper\.utilDecode\(\'([^\']+)\'\)\);'
        match = re.search (pattern,r.text)
        if match:
           decoded_jsonstr = base64.b64decode(match.group(1)).decode('utf-8')
  
        servicedata = json.loads(decoded_jsonstr)

        entries = []
        
        #Loop through services and append to Collection 
        for service in servicedata['services']:
            entries.append(
                Collection(
                    date=datetime.strptime(service['nextDate'], '%d/%m/%Y').date(),
                    t=service['serviceName'],
                    icon=ICON_MAP.get(service['serviceName']),
                )
            )

        return entries
