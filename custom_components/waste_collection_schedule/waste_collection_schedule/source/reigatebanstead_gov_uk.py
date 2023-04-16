import json
import requests
import bs4
import xml.etree.ElementTree as ET

from datetime import datetime
from time import time_ns
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Reigate & Banstead Borough Council"
DESCRIPTION = "Source for reigate-banstead.gov.uk services for the Reigate & Banstead Borough, UK."
URL = "https://reigate-banstead.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 68111681},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "FOOD 23 LTR CADDY": "mdi:food",
    "PLASTIC 55 LTR BOX": "mdi:recycle",
    "PAPER & CARDBOARD & 55 LTR BOX": "mdi:newspaper",
    "GLASS 55 LTR BOX": "mdi:glass-fragile",
    "RESIDUAL 180 LTR BIN": "mdi:trash-can",
    "PLASTICS & GLASS 240 LTR WHEELED BIN": "mdi:recycle",
    "PAPER & CARD 180 LTR WHEELED BIN": "mdi:newspaper",
    "GARDEN 240 LTR BIN": "mdi:leaf",
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

        payload = {
            "formValues": { "Section 1": {"uprnPWB": {"value": self._uprn},
                                          "minDate": {"value": "2023-04-16"},
                                          "maxDate": {"value": "2023-05-14"},
                                          "tokenString": {"value": token_string},
                                          }
                            }
        }        

        schedule_request = s.post(
            f"https://my.reigate-banstead.gov.uk/apibroker/runLookup?id=609d41ca89251&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload
        )

        #rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']
        rowdata = json.loads(schedule_request.content)['data']

        rowdata = ET.fromstring(rowdata)[0][0][1][0][0].text
        #rowdata = bs4.BeautifulSoup(rowdata)
        #rowdata = rowdata.get_text()

        print(rowdata)

        # Extract bin types and next collection dates
        entries = []
        for item in rowdata:                          
            entries.append(
                Collection(
                    t=rowdata[item]["ContainerName"],
                    date=datetime.strptime(
                        rowdata[item]["NextCollectionDate"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    icon=ICON_MAP.get(rowdata[item]["ContainerName"].upper()),
                )
            )

        return entries