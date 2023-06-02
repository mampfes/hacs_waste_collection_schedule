import json
import requests

from datetime import datetime
from time import time_ns, sleep
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Maidstone Borough Council"
DESCRIPTION = "Source for maidstone.gov.uk services for Maidstone Borough Council."
URL = "https://maidstone.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10022892379"}, # kfm, has mutliple collections
    "Test_002": {"uprn": 10014307164}, # 69sp
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
BIN_MAP = {
    "REFUSE": {"icon":"mdi:trash-can", "name": "Black bin and food"},
    "RECYCLING": {"icon":"mdi:recycle", "name": "Recycling bin and food"},
    "GARDEN": {"icon":"mdi:leaf", "name": "Garden bin"}
}
#ICON_MAP = {
#    "FOOD 23 LTR CADDY": "mdi:food",
#    "PLASTIC 55 LTR BOX": "mdi:recycle",
#    "PAPER & CARDBOARD & 55 LTR BOX": "mdi:newspaper",
#    "GLASS 55 LTR BOX": "mdi:glass-fragile",
#    "RESIDUAL 180 LTR BIN": "mdi:trash-can",
#    "PLASTICS & GLASS 240 LTR WHEELED BIN": "mdi:recycle",
#    "PAPER & CARD 180 LTR WHEELED BIN": "mdi:newspaper",
#    "GARDEN 240 LTR BIN": "mdi:leaf",
#}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        session_request = s.get(
            f"https://self.maidstone.gov.uk/apibroker/domain/self.maidstone.gov.uk?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://self.maidstone.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fself.maidstone.gov.uk%2Fservice%2Fcheck_your_bin_day&hostname=self.maidstone.gov.uk&withCredentials=true",
            headers=HEADERS
        )
        sid_data = sid_request.json()
        sid = sid_data['auth-session']

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds        
        payload = {
            "formValues": { "Your collections": {"uprn": {"value": self._uprn}}}
        }
        #schedule_request = s.post(
#            f"https://self.maidstone.gov.uk/apibroker/runLookup?id=61320b2acf8a3&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
#            headers=HEADERS,
#            json=payload
#        )
        # rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']

        # Extract bin types and next collection dates, separate requests for each because maidstone
        entries = []

        for bin in BIN_MAP.keys():
            # create payload for bin type
            payload = {
                "formValues": { "Your collections": {"bin": {"value": bin}, "uprn": {"value": self._uprn}}}
            }
            schedule_request = s.post(
                f"https://self.maidstone.gov.uk/apibroker/runLookup?id=61320b2acf8a3&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
                headers=HEADERS,
                json=payload
            )
            rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']

            for item in rowdata:
                entries.append(
                    Collection(
                        t=BIN_MAP[bin]['name'],
                        date=datetime.strptime(
                            rowdata[item]["Date"], "%d/%m/%Y"
                        ).date(),
                        icon=BIN_MAP.get(bin).get('icon'),
                    )
                )

            # as multiple requests going on here, throttle to 0.5s
            sleep(0.5)    

        return entries