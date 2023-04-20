import logging
import time
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "The Royal Borough of Kingston Council"
DESCRIPTION = (
    "Source for waste collection services for The Royal Borough of Kingston Council"
)
URL = "kingston.gov.uk"


HEADERS = {
    "user-agent": "Mozilla/5.0",
}

COOKIES = {}

TEST_CASES = {
    "Blagdon Road - number": {"uprn": 100021772910},
    "Blagdon Road - string": {"uprn": "100021772910"},
}

API_URLS = {
    "session": "https://kingston-self.achieveservice.com/service/In_my_Area_Results?uprn=100021772910&displaymode=collections&altVal=",
    "auth": "https://kingston-self.achieveservice.com/authapi/isauthenticated?uri=https%253A%252F%252Fkingston-self.achieveservice.com%252Fservice%252FIn_my_Area_Results%253Fuprn%253D100021772910%2526displaymode%253Dcollections%2526altVal%253D&hostname=kingston-self.achieveservice.com&withCredentials=true",
    "schedule": "https://kingston-self.achieveservice.com/apibroker/runLookup?id=601a61f9a3188&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()

        # This request sets up the cookies
        r0 = s.get(API_URLS["session"], headers=HEADERS)
        r0.raise_for_status()

        # This request gets the session key from the PHPSESSID (in the cookies)
        authRequest = s.get(API_URLS["auth"], headers=HEADERS)
        authData = authRequest.json()
        sessionKey = authData["auth-session"]
        now = time.time_ns() // 1_000_000

        # now query using the uprn
        payload = {
            "formValues": {
                "Section 1": {
                    "UPRN_FromUrl": {"value": self._uprn},
                    "borough_code": {"value": "RBK"},
                    "show_wasteCollection": {"value": "1"},
                    "echo_borough": {"value": "RBK"},
                    "echo_uprn": {"value": self._uprn},
                }
            }
        }

        scheduleRequest = s.post(
            API_URLS["schedule"] + "&_" + str(now) + "&sid=" + sessionKey,
            headers=HEADERS,
            json=payload,
        )
        data = scheduleRequest.json()["integration"]["transformed"]["rows_data"]["0"]
        entries = []

        if "echo_refuse_next_date" in data and data["echo_refuse_next_date"]:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        data["echo_refuse_next_date"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    t="refuse bin",
                    icon="mdi:trash-can",
                )
            )

        if "echo_food_waste_next_date" in data and data["echo_food_waste_next_date"]:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        data["echo_food_waste_next_date"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    t="food waste bin",
                    icon="mdi:trash-can",
                )
            )
        
        if "echo_paper_and_card_next_date" in data and data["echo_paper_and_card_next_date"]:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        data["echo_paper_and_card_next_date"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    t="paper and card recycling bin",
                    icon="mdi:recycle",
                )
            )

        if "echo_mixed_recycling_next_date" in data and data["echo_mixed_recycling_next_date"]:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        data["echo_mixed_recycling_next_date"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    t="mixed recycling bin",
                    icon="mdi:recycle",
                )
            )
        
        if "echo_garden_waste_next_date" in data and data["echo_garden_waste_next_date"]:
            entries.append(
                Collection(
                    date=datetime.strptime(
                        data["echo_garden_waste_next_date"], "%Y-%m-%d %H:%M:%S"
                    ).date(),
                    t="garden waste bin",
                    icon="mdi:leaf",
                )
            )

        return entries
