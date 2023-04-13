import json
import requests

from datetime import datetime
from time import time_ns
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Bexley"
DESCRIPTION = "Source for bexley.gov.uk services for the London Borough of Bexley, UK."
URL = "https://bexley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "200001604426"},
    "Test_002": {"uprn": 100020194783},
    "Test_003": {"uprn": "100020195768"},
    "Test_004": {"uprn": 100020200324},
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
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        session_request = s.get(
            f"https://mybexley.bexley.gov.uk/apibroker/domain/mybexley.bexley.gov.uk?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://mybexley.bexley.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmybexley.bexley.gov.uk%2Fservice%2FWhen_is_my_collection_day&hostname=mybexley.bexley.gov.uk&withCredentials=true",
            headers=HEADERS
        )
        sid_data = sid_request.json()
        sid = sid_data['auth-session']

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds        
        payload = {
            "formValues": { "What is your address?": {"txtUPRN": {"value": self._uprn}}}
        }
        schedule_request = s.post(
            f"https://mybexley.bexley.gov.uk/apibroker/runLookup?id=61320b2acf8a3&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload
        )
        rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']

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
