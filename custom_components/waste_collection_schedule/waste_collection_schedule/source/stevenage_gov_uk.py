import datetime
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stevenage"
DESCRIPTION = "Source for Stevenage."
URL = "https://www.stevenage.gov.uk/"
TEST_CASES = {
    "Chepstow Close": {"uprn": "100080879233"},
    "Rectory Lane": {"uprn": "100081137566"},
    "Neptune Gate": {"uprn": "200000585910"},
}

ICON_MAP = {
    "general waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
}

SESSION_URL = "https://stevenage-self.achieveservice.com/authapi/isauthenticated?uri=https%3A%2F%2Fstevenage-self.achieveservice.com%2Fen%2Fservice%2FCheck_your_household_bin_collection_days&hostname=stevenage-self.achieveservice.com&withCredentials=true"
TOKEN_URL = "https://stevenage-self.achieveservice.com/apibroker/runLookup?id=5e55337a540d4"
API_URL = "https://stevenage-self.achieveservice.com/apibroker/runLookup"

class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        data = {
            "formValues": {
                "Section 1": {
                    "token": {
                        "value": ""
                    },
                    "LLPGUPRN": {
                        "value": self._uprn,
                    },
                    "MinimumDateLookAhead": {
                        "value": time.strftime("%Y-%m-%d"),
                    },
                    "MaximumDateLookAhead": {
                        "value": str(int(time.strftime("%Y")) + 1) + time.strftime("-%m-%d"),
                    }
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://stevenage-self.achieveservice.com/fillform/?iframe_id=fillform-frame-1&db_id=",
        }
        s = requests.session()
        r = s.get(SESSION_URL)
        r.raise_for_status()
        session_data = r.json()
        sid = session_data["auth-session"]

        t = s.get(TOKEN_URL)
        t.raise_for_status()
        token_data = t.json()
        data["formValues"]["Section 1"]["token"]["value"] = token_data["integration"]["transformed"]["rows_data"]["0"]["token"]

        params = {
            "id": "64ba8cee353e6",
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            # unix_timestamp
            "_": str(int(time.time() * 1000)),
            "sid": sid,
        }

        r = s.post(API_URL, json=data, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        rows_data = data["integration"]["transformed"]["rows_data"]
        if not isinstance(rows_data, dict):
            raise ValueError("Invalid data returned from API")

        entries = []
        for key in rows_data:
            value = rows_data[key]
            bin_type = value["bintype"].strip()

            try:
                date = datetime.datetime.strptime(value["collectiondate"], "%A %d %B %Y").date()
            except ValueError:
                continue
            
            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type.lower()),
                )
            )

        return entries