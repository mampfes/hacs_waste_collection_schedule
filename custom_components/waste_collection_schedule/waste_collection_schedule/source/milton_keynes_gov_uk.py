# modified version of bexley_gov_uk.py

from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Milton Keynes council"
DESCRIPTION = "Source for Milton Keynes council."
URL = "milton-keynes.gov.uk"
TEST_CASES = {
    "North Row, Central": {"uprn": 25032037},
    "Adelphi Street, Campbell Park": {"uprn": 25044504},
}


ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "RECYCLING": "mdi:recycle",
    "FOOD": "mdi:leaf",
    "GARDEN": "mdi:leaf",
}


SITE_URL = (
    "https://mycouncil.milton-keynes.gov.uk/service/Waste_Collection_Round_Checker"
)
HEADERS = {
    "user-agent": "Mozilla/5.0",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            "https://mycouncil.milton-keynes.gov.uk/apibroker/domain/mycouncil.milton-keynes.gov.uk",
            params={
                "_": timestamp,
            },
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://mycouncil.milton-keynes.gov.uk/authapi/isauthenticated",
            params={
                "uri": "https://mycouncil.milton-keynes.gov.uk/service/Waste_Collection_Round_Checker",
                "hostname": "mycouncil.milton-keynes.gov.uk",
                "withCredentials": "true",
            },
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {"formValues": {"Section 1": {"uprnCore": {"value": self._uprn}}}}
        schedule_request = s.post(
            "https://mycouncil.milton-keynes.gov.uk/apibroker/runLookup",
            headers=HEADERS,
            params={
                # "id": "61320b2acf8a3",
                "id": "64d9feda3a507",
                "repeat_against": "",
                "noRetry": "false",
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
        for index, item in rowdata.items():
            # print(item)
            bin_type = item["AssetTypeName"]
            icon = None

            for key, icon_name in ICON_MAP.items():
                if (
                    key in item["AssetTypeName"].upper()
                    or key in item["TaskTypeName"].upper()
                    or key in item["ServiceName"].upper()
                ):
                    icon = icon_name
                    break

            dates = [
                datetime.strptime(item["NextInstance"], "%Y-%m-%d").date(),
                datetime.strptime(item["LastInstance"], "%Y-%m-%d").date(),
            ]
            for date in dates:
                entries.append(
                    Collection(t=bin_type, date=date, icon=icon),
                )
        return entries
