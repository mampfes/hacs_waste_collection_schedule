from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Orillia, Ontario"
DESCRIPTION = "Source for Orillia, Ontario."
URL = "https://www.orillia.ca/"
TEST_CASES = {
    "!secret orilla_email !secret orilla_password": {
        "email": "!secret orilla_email",
        "password": "!secret orilla_password",
    }
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


COLLECTION_URL = "https://citizenportal-product-api.esolg.ca/api/v1/orillianow-orillia/mywastedashboard/get-mywaste-widget-content-async/198"
LOGIN_URL = "https://citizenportal-product-api.esolg.ca/api/v1/orillianow-orillia/account/sign-in"


class Source:
    def __init__(self, email: str, password: str):
        self._email: str = email
        self._password: str = password

    def fetch(self) -> list[Collection]:
        r = requests.post(
            LOGIN_URL,
            json={"email": self._email, "password": self._password, "tenantId": 7},
        )
        r.raise_for_status()
        data = r.json()
        if "errorMessage" in data and data["errorMessage"] != "":
            raise Exception(data["errorMessage"])

        token = data["token"]
        r = requests.get(COLLECTION_URL, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()

        data = r.json()

        entries = []
        for d in data["data"]["eventsResults"]["data"]["schedules"]:
            date = datetime.strptime(d["date"], "%m-%d-%Y").date()
            for coll_types in d["collectionTypes"]:
                bin_type = coll_types["collectionType"]
                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date, t=bin_type, icon=icon))
        return entries
