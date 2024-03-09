from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Tunbridge Wells"
DESCRIPTION = "Source for Tunbridge Wells."
URL = "https://tunbridgewells.gov.uk/"
TEST_CASES = {
    "10090058289": {"uprn": "10090058289"},
    "100061204678": {"uprn": 100061204678},
}


ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "GARDEN": "mdi:leaf",
    "RECYCLING": "mdi:recycle",
}


API_URL = "https://mytwbc.tunbridgewells.gov.uk/AchieveForms//definition.json&process=1&process_uri=sandbox-proac-c47b63f017ed"
HEADERS = {
    "user-agent": "Mozilla/5.0",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        # This request gets the session ID
        sid_request = s.get(
            "https://mytwbc.tunbridgewells.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmytwbc.tunbridgewells.gov.uk%2FAchieveForms%2F%3Fmode%3Dfill%26consentMessage%3Dyes%26form_uri%3Dsandbox-publish%3A%2F%2FAF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed%2FAF-Stage-88caf66c-378f-4082-ad1d-07b7a850af38%2Fdefinition.json%26process%3D1%26process_uri%3Dsandbox-processes%3A%2F%2FAF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed%26process_id%3DAF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed&hostname=mytwbc.tunbridgewells.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Property": {
                    key: {"value": self._uprn}
                    for key in ["addressPicker", "propertyReference", "siteReference"]
                }
            }
        }
        schedule_request = s.post(
            f"https://mytwbc.tunbridgewells.gov.uk/apibroker/runLookup?id=6314720683f30&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        rowdata = schedule_request.json()["integration"]["transformed"]["rows_data"]

        # Extract bin types and next collection dates
        entries = []
        for _, item in rowdata.items():
            bin_type = item["collectionType"]
            entries.append(
                Collection(
                    t=bin_type,
                    date=datetime.strptime(
                        item["nextDateUnformatted"], "%d/%m/%Y"
                    ).date(),
                    icon=ICON_MAP.get(bin_type.upper()),
                )
            )

        return entries
