import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Blackpool Council"
DESCRIPTION = "Source for blackpool.gov.uk services for Blackpool Council, UK."
URL = "https://blackpool.gov.uk"
TEST_CASES = {
    "Test1": {"postcode": "FY1 4DZ", "uprn": "100010802829"},
    "Test2": {"postcode": "FY3 9RQ", "uprn": "100010842301"},
    "Test3": {"postcode": "FY1 2HR", "uprn": 100012606962},
}

API_URL = "https://api.blackpool.gov.uk/api/bartec"
REGEX_JOB_NAME = r"^Empty((?: [A-Za-z]+)+) \d+\w$"
NAME_MAP = {
    "Domestic Refuse": "Grey bin or Red sack",
    "Dry Recycling": "Blue bin",
}
ICON_MAP = {
    "Domestic Refuse": "mdi:trash-can",
    "Dry Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, postcode, uprn):
        self._postcode = str(postcode)
        self._uprn = str(uprn)

    def fetch(self):
        # GET request returns token
        s = requests.Session()
        r0 = s.get(f"{API_URL}/security/token")
        r0.raise_for_status()

        # POST request returns schedule for matching postcode/uprn
        payload = {
            "UPRN": self._uprn,
            "USRN": "",
            "PostCode": self._postcode,
            "StreetNumber": "",
            "CurrentUser": {
                "UserId": "",
                "Token": r0.text.strip('"'),
            },
        }
        r1 = s.post(f"{API_URL}/collection/PremiseJobs", json=payload)
        r1.raise_for_status()

        # Extract job name and date from response
        entries = []
        for job in r1.json()["jobsField"]:
            # "Empty Domestic Refuse 240L" -> "Domestic Refuse"
            jobName = (
                re.search(REGEX_JOB_NAME, job["jobField"]["nameField"]).group(1).strip()
            )
            entries.append(
                Collection(
                    date=datetime.strptime(
                        job["jobField"]["scheduledStartField"], "%Y-%m-%dT%H:%M:%S"
                    ).date(),
                    t=NAME_MAP.get(jobName),
                    icon=ICON_MAP.get(jobName),
                )
            )

        return entries
