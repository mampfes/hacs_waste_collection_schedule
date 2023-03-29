from datetime import datetime, timedelta

import requests
import re
import json
import base64
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Gateshead Council"
DESCRIPTION = "Source for gateshead.gov.uk services for Gateshead"
URL = "gateshead.gov.uk"

TEST_CASES = {
    "Test_001": {"uprn": "100000077407"},
    "Test_002": {"uprn": "100000058404"},
}

ICON_MAP = {
    "Household": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        session = requests.Session()
        
        # Start a session
        r = session.get("https://www.gateshead.gov.uk/article/3150/Bin-collection-day-checker")
        
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Extract form submission url and form data
        form_url = soup.find("form", attrs={"id": "BINCOLLECTIONCHECKER_FORM"})["action"]
        pageSessionId = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_PAGESESSIONID"})["value"]
        sessionId = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_SESSIONID"})["value"]
        nonce = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_NONCE"})["value"]
        ticks = soup.find("input", attrs={"name": "BINCOLLECTIONCHECKER_ADDRESSSEARCH_TICKS"})["value"]
        
        form_data = {
            "BINCOLLECTIONCHECKER_PAGESESSIONID": pageSessionId,
            "BINCOLLECTIONCHECKER_SESSIONID": sessionId,
            "BINCOLLECTIONCHECKER_NONCE": nonce,
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_TICKS": ticks,
            "BINCOLLECTIONCHECKER_FORMACTION_NEXT": "BINCOLLECTIONCHECKER_ADDRESSSEARCH_NEXTBUTTON",
            "BINCOLLECTIONCHECKER_ADDRESSSEARCH_UPRN": self._uprn,
        }

        # Submit form
        r = session.post(form_url, data=form_data)
        r.raise_for_status()
        
        # Extract encoded response data
        soup = BeautifulSoup(r.text, features="html.parser")
        pattern = re.compile(r"var BINCOLLECTIONCHECKERFormData = \"(.*?)\";$", re.MULTILINE | re.DOTALL)
        script = soup.find("script", text=pattern)

        response_data = pattern.search(script.text).group(1)

        # Decode base64 encoded response data and convert to JSON
        decoded_data = base64.b64decode(response_data)
        data = json.loads(decoded_data)
        
        # Extract entries
        entries = []
        for bin in data["HOUSEHOLDCOLLECTIONS_1"]["DISPLAYHOUSEHOLD2"]["propertyCollections"]["future"]:
            dt = datetime.strptime(bin['collectionDate'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if dt.hour == 23: # Some collections are returned as 11pm night before the collection
                dt += timedelta(hours=1)
            date = dt.date()
            types = bin['wasteTypeCode'].split("|")
            for type in types:
                entries.append(
                    Collection(
                        date=date,
                        t=type,
                        icon=ICON_MAP.get(type),
                    )
                )
                    

        return entries
