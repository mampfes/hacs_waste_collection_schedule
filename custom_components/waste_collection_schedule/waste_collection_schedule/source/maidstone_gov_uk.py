import json
from datetime import datetime
from time import time_ns

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Maidstone Borough Council"
DESCRIPTION = "Source for maidstone.gov.uk services for Maidstone Borough Council."
URL = "https://maidstone.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10022892379"},
    "Test_002": {"uprn": 10014307164},
    "Test_003": {"uprn": "200003674881"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

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
        self._uprn = str(uprn).strip()

    def fetch(self):
        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000
        s.get(
            f"https://my.maidstone.gov.uk/apibroker/domain/my.maidstone.gov.uk?_={timestamp}&sid=979631f89458fc974cc2aa69ebbd7996",
            headers=HEADERS,
        )

        # Get Session ID
        timestamp = time_ns() // 1_000_000
        sid_request = s.get(
            "https://my.maidstone.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmy.maidstone.gov.uk%2Fservice%2FFind-your-bin-day&hostname=my.maidstone.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        sid_data = sid_request.json()
        sid = sid_data["auth-session"]

        # Retrieve Schedule
        timestamp = time_ns() // 1_000_000
        payload = {
            "formValues": {
                "Lookup": {
                    "AddressData": {"value": self._uprn},
                    "AddressUPRN": {"value": self._uprn},
                }
            }
        }

        schedule_request = s.post(
            f"https://my.maidstone.gov.uk/apibroker/runLookup?id=654b7b6478deb&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )

        try:
            rowdata = json.loads(schedule_request.content)["integration"][
                "transformed"
            ]["rows_data"][self._uprn]
        except KeyError:
            return []

        entries = []
        collections = {}

        for key, value in rowdata.items():
            # Extract the bin type prefix (e.g., "DomesticResidual")
            collection_key = key.split("_")[0]

            # Check if this service is active for the property
            # The API returns keys like "DomesticResidual_Active": "Y" or "N"
            active_key = f"{collection_key}_Active"
            if rowdata.get(active_key) == "N":
                continue

            # Parse Dates
            # Logic updated to exclude "Default" and "Original" dates to prevent duplicates during holiday rescheduling
            if (
                key.endswith("_NextCollectionDateMM")
                and "Default" not in key
                and "Original" not in key
                and value != ""
            ):
                if collection_key not in collections:
                    collections[collection_key] = {"dates": []}

                try:
                    collections[collection_key]["dates"].append(
                        datetime.strptime(value, "%d/%m/%Y").date()
                    )
                except ValueError:
                    pass

            # Parse Description
            if "_Description" in key and "Default" not in key:
                if collection_key not in collections:
                    collections[collection_key] = {"dates": []}
                collections[collection_key]["description"] = value

        for key, collection in collections.items():
            bin_name = collection.get("description") or key

            # Map icons
            clean_name = (
                bin_name.lower()
                .replace("domestic ", "")
                .replace("communal ", "")
                .replace("waste", "")
                .strip()
            )
            icon = ICON_MAP.get(clean_name, "mdi:trash-can")

            for collectionDate in set(collection["dates"]):
                entries.append(
                    Collection(
                        t=bin_name,
                        date=collectionDate,
                        icon=icon,
                    )
                )

        return entries
