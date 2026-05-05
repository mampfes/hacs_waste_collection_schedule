import json
from datetime import datetime, timedelta
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Dudley Metropolitan Borough Council"
DESCRIPTION = "Source for Dudley Metropolitan Borough Council, UK."
URL = "https://dudley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "90090715"},
    "Test_002": {"uprn": 90104555},
    "Test_003": {"uprn": "90164803"},
    "Test_004": {"uprn": 90092621},
}
ICON_MAP = {
    "RECYCLING": "mdi:recycle",
    "FOOD": "mdi:food",
    "REFUSE": "mdi:trash-can",
}

LOOKUP_ID = "69a04ac70086b"
BASE_URL = "https://my.dudley.gov.uk"

COLLECTION_TYPES = {
    "recyclingDate": "Recycling",
    "foodDate": "Food",
    "refuseDate": "Refuse",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).zfill(12)

    def fetch(self):
        s = requests.Session()

        # Get session ID
        timestamp = time_ns() // 1_000_000
        sid_request = s.get(
            f"{BASE_URL}/authapi/isauthenticated?uri={BASE_URL}&hostname=my.dudley.gov.uk&withCredentials=true&_={timestamp}",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # Fetch collection schedule
        timestamp = time_ns() // 1_000_000
        now = datetime.now()
        from_date = now.strftime("%Y-%m-%d")
        to_date = (now + timedelta(days=60)).strftime("%Y-%m-%d")
        payload = {
            "formValues": {
                "Section 1": {
                    "uprnToCheck": {"value": self._uprn},
                    "NextCollectionFromDate": {"value": from_date},
                    "NextCollectionToDate": {"value": to_date},
                }
            }
        }
        schedule_request = s.post(
            f"{BASE_URL}/apibroker/runLookup?id={LOOKUP_ID}&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        schedule_request.raise_for_status()
        data = json.loads(schedule_request.content)
        rows_data = data["integration"]["transformed"]["rows_data"]

        entries = []
        for row in rows_data.values():
            for date_key, waste_type in COLLECTION_TYPES.items():
                date_str = row.get(date_key, "")
                if not date_str:
                    continue
                entries.append(
                    Collection(
                        date=datetime.strptime(date_str, "%d/%m/%Y").date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
