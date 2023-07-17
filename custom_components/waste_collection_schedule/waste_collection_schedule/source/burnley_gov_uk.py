import json
import requests

from datetime import datetime
from time import time_ns
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Burnley Council"
DESCRIPTION = "Source for burnley.gov.uk services for the Burnley, UK."
URL = "https://burnley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "100010341681"},
    "Test_002": {"uprn": 100020194783},
    "Test_003": {"uprn": "100020195768"},
    "Test_004": {"uprn": 100020200324},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        session_request = s.get(
            f"https://your.burnley.gov.uk/apibroker/domain/your.burnley.gov.uk?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://your.burnley.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fyour.burnley.gov.uk%252Fen%252FAchieveForms%252F%253Fform_uri%253Dsandbox-publish%253A%252F%252FAF-Process-b41dcd03-9a98-41be-93ba-6c172ba9f80c%252FAF-Stage-edb97458-fc4d-4316-b6e0-85598ec7fce8%252Fdefinition.json%2526redirectlink%253D%25252Fen%2526cancelRedirectLink%253D%25252Fen%2526consentMessage%253Dyes&hostname=your.burnley.gov.uk&withCredentials=true",
            headers=HEADERS
        )
        sid_data = sid_request.json()
        sid = sid_data['auth-session']

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds        
        payload = {
            "formValues": {
                "Section 1": {
                    "case_uprn1": {
                        "value": self._uprn
                    }
                }
            }
        }
        schedule_request = s.post(
            f"https://your.burnley.gov.uk/apibroker/runLookup?id=607fe757df87c&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload
        )
        rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']

        # Extract bin types and next collection dates
        entries = []
        for item in rowdata:
            info = rowdata[item]["display"].split(" - ")
            waste = info[0]
            dt = info[1]
            entries.append(
                Collection(
                    t=waste,
                    date=datetime.strptime(dt, "??").date(),
                    icon=waste.upper(),
                )
            )

        return entries
