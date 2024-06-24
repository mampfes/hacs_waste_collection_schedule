import json
from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Many thanks to dt215git for their work on the Bexley version of this provider which helped me write this.

TITLE = "Maidstone Borough Council"
DESCRIPTION = "Source for maidstone.gov.uk services for Maidstone Borough Council."
URL = "https://maidstone.gov.uk"
TEST_CASES = {
    "Test_001": {
        "uprn": "10022892379"
    },  # has multiple collections on same week per bin type
    "Test_002": {
        "uprn": 10014307164
    },  # has duplicates of the same collection (two bins for this block of flats?)
    "Test_003": {
        "uprn": "200003674881"
    },  # has garden waste collection, at time of coding
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

# map names and icons, maidstone group food recycling for both
ICON_MAP = {
    "clinical": "mdi:medical-bag",
    "bulky": "mdi:sofa",
    "residual": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food",
}


class Source:
    def __init__(self, uprn):
        # self._uprn = str(uprn).zfill(12)
        self._uprn = str(uprn).strip()

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        s.get(
            f"https://my.maidstone.gov.uk/apibroker/domain/my.maidstone.gov.uk?_={timestamp}&sid=979631f89458fc974cc2aa69ebbd7996",
            headers=HEADERS,
        )
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds

        # This request gets the session ID
        sid_request = s.get(
            "https://my.maidstone.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmy.maidstone.gov.uk%2Fservice%2FFind-your-bin-day&hostname=my.maidstone.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {
                "Lookup": {
                    "AddressData": {"value": self._uprn},
                    "AddressUPRN": {"value": self._uprn},
                }
            }
        }

        entries = []
        schedule_request = s.post(
            f"https://my.maidstone.gov.uk/apibroker/runLookup?id=654b7b6478deb&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        rowdata = json.loads(schedule_request.content)["integration"]["transformed"][
            "rows_data"
        ][self._uprn]
        collections: dict[str, dict[str, list[datetime.date] | str]] = {}

        for key, value in rowdata.items():
            if (
                "NextCollectionDateMM" in key or "LastCollectionOriginalDateMM" in key
            ) and value != "":
                collection_key = key.split("_")[0]
                if collection_key not in collections:
                    collections[collection_key] = {"dates": []}
                collections[collection_key]["dates"].append(
                    datetime.strptime(value, "%d/%m/%Y").date()
                )
            if "_Description" in key:
                collection_key = key.split("_")[0]
                if collection_key not in collections:
                    collections[collection_key] = {"dates": []}
                collections[collection_key]["description"] = value

        for key, collection in collections.items():
            bin = collection.get("description") or key
            icon = ICON_MAP.get(
                bin.lower()
                .replace("domestic ", "")
                .replace("communal ", "")
                .replace("waste", "")
                .strip()
            )
            for collectionDate in set(collection["dates"]):
                entries.append(
                    Collection(
                        t=bin,
                        date=collectionDate,
                        icon=icon,
                    )
                )
        return entries
