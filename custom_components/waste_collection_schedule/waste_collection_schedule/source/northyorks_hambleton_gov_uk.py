# Highly based on milton_keynes_gov_uk.py

from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "North Yorkshire Council - Hambleton"
DESCRIPTION = "Source for North Yorkshire Council - Hambleton."
URL = "https://northyorks.gov.uk"
TEST_CASES = {
    "010070735142": {"uprn": "010070735142"},
    "100050360667": {"uprn": "100050360667"},
    "010070732324, leading 0 missing": {"uprn": 10070732324},
}


ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "GARDEN WASTE": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

API_URL = "https://hambletondc-self.achieveservice.com/service/Bin_collection_finder"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            "https://hambletondc-self.achieveservice.com/apibroker/domain/hambletondc-self.achieveservice.com",
            params={
                "_": timestamp,
            },
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://hambletondc-self.achieveservice.com/authapi/isauthenticated",
            params={
                "uri": "https://hambletondc-self.achieveservice.com/service/Bin_collection_finder",
                "hostname": "hambletondc-self.achieveservice.com",
                "withCredentials": "true",
            },
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Address search": {
                    "pccUPRN": {"value": self._uprn},
                    "selectedUPRN": {"value": self._uprn},
                }
            }
        }
        schedule_request = s.post(
            "https://hambletondc-self.achieveservice.com/apibroker/runLookup",
            headers=HEADERS,
            params={
                "id": "62b1d2c960a47",
                "repeat_against": "",
                "noRetry": "true",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AF-Renderer::Self",
                "_": str(timestamp),
                "sid": str(sid),
            },
            json=payload,
        )
        rowdata = schedule_request.json()["integration"]["transformed"]["rows_data"]

        # Extract bin types and next collection dates
        entries = []
        for item in rowdata.values():
            bin_type = item["Collection_Type"]
            date_str = item["Collection_Date"]
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            icon = ICON_MAP.get(bin_type.upper().replace("COLLECTION", ""))
            entries.append(
                Collection(t=bin_type, date=date, icon=icon),
            )
        return entries
