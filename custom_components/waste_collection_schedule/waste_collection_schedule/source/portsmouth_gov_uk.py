import time
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Portsmouth City Council"
DESCRIPTION = "Source for waste collection services for Portsmouth City Council"
URL = "https://www.portsmouth.gov.uk"
TEST_CASES = {
    "Fawcett Road - number": {"uprn": 1775027540},
    "Fawcett Road - string": {"uprn": "1775027540"},
    "Westbourne Road - number": {"uprn": 1775084532},
    "Westbourne Road - string": {"uprn": "1775084532"},
}

API_URLS = {
    "session": "https://my.portsmouth.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-26e27e70-f771-47b1-a34d-af276075cede/AF-Stage-cd7cc291-2e59-42cc-8c3f-1f93e132a2c9/definition.json&redirectlink=%2F&cancelRedirectLink=%2F",
    "auth": "https://my.portsmouth.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmy.portsmouth.gov.uk%2Fen%2FAchieveForms%2F%3Fform_uri%3Dsandbox-publish%3A%2F%2FAF-Process-26e27e70-f771-47b1-a34d-af276075cede%2FAF-Stage-cd7cc291-2e59-42cc-8c3f-1f93e132a2c9%2Fdefinition.json%26redirectlink%3D%252F%26cancelRedirectLink%3D%252F&hostname=my.portsmouth.gov.uk&withCredentials=true",
    "schedule": "https://my.portsmouth.gov.uk/apibroker/runLookup?id=5e81ed10c0241&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_=1682697046055&sid=93c73ba547e8c23e85a50a1de67a5ca7",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}


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
        payload = {"formValues": {"Section 1": {"col_uprn": {"value": self._uprn}}}}
        scheduleRequest = s.post(
            API_URLS["schedule"] + "&_" + str(now) + "&sid=" + sessionKey,
            headers=HEADERS,
            json=payload,
        )
        data = scheduleRequest.json()["integration"]["transformed"]["rows_data"]["0"]

        rubbishDates = data["listRefDatesHTML"].split("<p>")[0].split("<br />")
        recyclingDates = data["listRecDatesHTML"].split("<p>")[0].split("<br />")

        entries = []
        for date in rubbishDates:
            if len(date) > 0:
                entries.append(
                    Collection(
                        date=datetime.strptime(date.rstrip("* "), "%A %d %B %Y").date(),
                        t="refuse bin",
                        icon="mdi:trash-can",
                    )
                )

        for date in recyclingDates:
            if len(date) > 0:
                entries.append(
                    Collection(
                        date=datetime.strptime(date.rstrip("* "), "%A %d %B %Y").date(),
                        t="recycling bin",
                        icon="mdi:recycle",
                    )
                )

        return entries
