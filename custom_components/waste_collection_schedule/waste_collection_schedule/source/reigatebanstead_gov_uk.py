import json
import requests
import bs4
import xml.etree.ElementTree as ET

from datetime import datetime, timedelta
from time import time_ns
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Reigate & Banstead Borough Council"
DESCRIPTION = "Source for reigate-banstead.gov.uk services for the Reigate & Banstead Borough, UK."
URL = "https://reigate-banstead.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 68110755},
    "Test_002": {"uprn": "000068110755"},
    "Test_003": {"uprn": "68101147"}, #commercial refuse collection
    "Test_004": {"uprn": "000068101147"}, #commercial refuse collection
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "FOOD WASTE": "mdi:food",
    "MIXED RECYCLING": "mdi:recycle",
    "GLASS": "mdi:recycle", #commercial
    "MIXED CANS": "mdi:recycle", #commercial
    "PLASTIC": "mdi:recycle", #commercial
    "PAPER AND CARDBOARD": "mdi:newspaper",
    "TRADE - PAPER AND CARDBOARD": "mdi:newspaper", #commercial
    "REFUSE": "mdi:trash-can",
    "TRADE - REFUSE": "mdi:trash-can", #commercial
    "GARDEN WASTE": "mdi:leaf",
}

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        session_request = s.get(
            f"https://my.reigate-banstead.gov.uk/apibroker/domain/my.reigate-banstead.gov.uk?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://my.reigate-banstead.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmy.reigate-banstead.gov.uk%2Fservice%2FBins_and_recycling___collections_calendar&hostname=my.reigate-banstead.gov.uk&withCredentials=true",
            headers=HEADERS
        )
        sid_data = sid_request.json()
        sid = sid_data['auth-session']

        # this request gets the 'tokenString' for use later
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds  
        token_request = s.get(
            f"https://my.reigate-banstead.gov.uk/apibroker/runLookup?id=595ce0f243541&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS
        )
        token_data = token_request.json()
        token_string = ET.fromstring(token_data['data'])[0][0][1][0][0].text

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds        
        
        min_date = datetime.today().strftime("%Y-%m-%d") #today
        max_date = datetime.today() + timedelta(days=28) # max of 28 days ahead
        max_date = max_date.strftime("%Y-%m-%d")

        payload = {
            "formValues": { "Section 1": {"uprnPWB": {"value": self._uprn},
                                          "minDate": {"value": min_date},
                                          "maxDate": {"value": max_date},
                                          "tokenString": {"value": token_string},
                                          }
                            }
        }        

        schedule_request = s.post(
            f"https://my.reigate-banstead.gov.uk/apibroker/runLookup?id=609d41ca89251&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload
        )

        # oh good, response in JSON... that contains XML... that contains HTML...
        rowdata = json.loads(schedule_request.content)['data']
        html_rowdata = ET.fromstring(rowdata)[0][0][1][0][0].text
        rowdata = bs4.BeautifulSoup(html_rowdata, "html.parser")
        datedata = rowdata.findAll("h3")
        bindata = rowdata.findAll("ul")

        # Extract bin types and next collection dates
        x=0
        entries = []
        for item in bindata:
            bin_date = datedata[x].text.strip()
            x=x+1
            bins = item.findAll('span')
            for bin in bins:
                bin_type=bin.text.strip()
                entries.append(
                    Collection(
                        t=bin_type,
                        date=datetime.strptime(bin_date, "%A %d %B %Y").date(),
                        icon=ICON_MAP.get(bin.text.upper())
                    )
                )

        return entries