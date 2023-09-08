import json
from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City Of Lincoln Council"
DESCRIPTION = "Source for City Of Lincoln Council."
URL = "https://www.lincoln.gov.uk/"
TEST_CASES = {
    "LN5 7SH 000235024846": {"postcode": "LN5 7SH", "uprn": "000235024846"},
    "LN2 4SA, 000235042214": {"postcode": "LN24Sa", "uprn": 235042214},
    "LN2 4EB 000235036597": {"postcode": " Ln 24 eB ", "uprn": 235036597},
}


ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Garden": "mdi:leaf",
    "Recycling": "mdi:recycle",
}


API_URL = "https://www.lincoln.gov.uk/b/view-bin-collection-days"

HEADERS = {
    "user-agent": "Mozilla/5.0",
}


BIN_TYPES = [
    ("refusenextdate", "Refuse"),
    ("recyclenextdate", "Recycling"),
    ("gardennextdate", "Garden"),
]


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.replace(" ", "").upper()
        self._postcode = self._postcode[:3] + " " + self._postcode[3:]
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()
        s.headers.update(HEADERS)

        # This request gets the session ID
        sid_request = s.get(
            "https://contact.lincoln.gov.uk/authapi/isauthenticated",
            params={
                "uri": "https://contact.lincoln.gov.uk/AchieveForms/?mode=fill&consentMessage=yes&form_uri=sandbox-publish://AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196/AF-Stage-a1c0af0f-fec1-4419-80c0-0dd4e1d965c9/definition.json&process=1&process_uri=sandbox-processes://AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196&process_id=AF-Process-503f9daf-4db9-4dd8-876a-6f2029f11196",
                "hostname": "contact.lincoln.gov.uk",
                "withCredentials": True,
            },
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            "https://contact.lincoln.gov.uk/apibroker/domain/contact.lincoln.gov.uk",
            params={"_": timestamp, "sid": sid},
        )

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Section 1": {
                    "chooseaddress": {"value": self._uprn},
                    "postcode": {"value": self._postcode},
                }
            }
        }
        params = {
            "id": "62aafd258f72c",
            "repeat_against": "",
            "noRetry": False,
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": timestamp,
            "sid": sid,
        }
        schedule_request = s.post(
            "https://contact.lincoln.gov.uk/apibroker/runLookup",
            params=params,
            json=payload,
        )

        rowdata = json.loads(schedule_request.content)["integration"]["transformed"][
            "rows_data"
        ]

        # Extract bin types and next collection dates
        entries = []
        for uprn, data in rowdata.items():
            if uprn != self._uprn:
                continue
            bin_types = BIN_TYPES.copy()
            if data["recyclenextdate"] != data["refusenextdate"]:
                bin_types.append(("recyclenextdate", "Refuse"))
            for key, bin_type in bin_types:
                if not data[key]:
                    continue
                entries.append(
                    Collection(
                        t=bin_type,
                        date=datetime.strptime(data[key], "%Y-%m-%d").date(),
                        icon=ICON_MAP.get(bin_type),
                    )
                )
        return entries
