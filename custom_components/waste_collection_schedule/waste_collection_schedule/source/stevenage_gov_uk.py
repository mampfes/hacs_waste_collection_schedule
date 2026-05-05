import datetime
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Stevenage Borough Council"
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

BASE_URL = "https://stevenage-self.achieveservice.com"
INITIAL_URL = f"{BASE_URL}/en/service/Check_your_household_bin_collection_days"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
TOKEN_URL = f"{BASE_URL}/apibroker/runLookup?id=5e55337a540d4"
API_URL = f"{BASE_URL}/apibroker/runLookup"
LOOKUP_ID = "64ba8cee353e6"
HOSTNAME = "stevenage-self.achieveservice.com"


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        session = requests.Session()
        sid = init_session(session, INITIAL_URL, AUTH_URL, HOSTNAME)

        # Stevenage-specific: GET a one-time token before the main lookup
        t = session.get(TOKEN_URL)
        t.raise_for_status()
        token = t.json()["integration"]["transformed"]["rows_data"]["0"]["token"]

        form_values = {
            "Section 1": {
                "token": {"value": token},
                "LLPGUPRN": {"value": self._uprn},
                "MinimumDateLookAhead": {"value": time.strftime("%Y-%m-%d")},
                "MaximumDateLookAhead": {
                    "value": str(int(time.strftime("%Y")) + 1) + time.strftime("-%m-%d"),
                },
            }
        }

        result = run_lookup(session, API_URL, sid, LOOKUP_ID, form_values)
        rows_data = result["integration"]["transformed"]["rows_data"]
        if not isinstance(rows_data, dict):
            raise ValueError("Invalid data returned from API")

        entries = []
        for key in rows_data:
            value = rows_data[key]
            bin_type = value["bintype"].strip()

            try:
                date = datetime.datetime.strptime(
                    value["collectiondate"], "%A %d %B %Y"
                ).date()
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
