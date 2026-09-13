from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Plymouth City Council"
DESCRIPTION = "Source for waste collection services for Plymouth City Council"
URL = "https://www.plymouth.gov.uk/"

TEST_CASES = {
    "Test_001": {"uprn": 100040429524},
    "Test_002": {"uprn": "100040425325"},
    "Test_003": {"uprn": 100040472543},
    "Test_004": {"uprn": "100040462838"},
    "Test_005": {"uprn": 100040461084},
}

HOSTNAME = "plymouth-self.achieveservice.com"
BASE_URL = f"https://{HOSTNAME}"
INITIAL_URL = f"{BASE_URL}/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-084d6742-3572-41ba-ac1a-430750451f9d/AF-Stage-67ba684d-0a5b-48f8-9c50-1c01cc43c396/definition.json&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/{HOSTNAME}"
API_URL = f"{BASE_URL}/apibroker/runLookup"

# Plymouth rebuilt their "Check your collection days" form on 2026-07-31 to add
# food waste. The old single "5c99439d85f83" lookup (UPRN + next-N-collections)
# no longer returns data. It has been replaced by a two-step lookup chain:
#   1. "collectiveAuthenticator" - no inputs, returns a short-lived opaque
#      "collectiveKey" token required by every other lookup in the new form.
#   2. "collectionDays" - takes the UPRN, the collectiveKey, and an explicit
#      start/end date window, and returns the actual collection rows.
AUTHENTICATOR_LOOKUP_ID = "6936e38f6d376"
COLLECTION_DAYS_LOOKUP_ID = "698b9c49a3c13"

# How far ahead to request collections for. The live form itself only asks for
# a 15-day window (today .. today+15), we ask for a wider one to surface more
# upcoming collections in one fetch.
LOOKAHEAD_DAYS = 60

# collectiveWasteType values look like "Empty Food 23L" / "Empty Residual 240L"
# / "Empty Recycling 1100L" / "Empty Garden 240L" - the bin size suffix varies
# per property, so match on the waste-type keyword rather than the full string.
ICON_MAP = {
    "residual": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "garden": Icons.GARDEN,
    "food": Icons.BIO_KITCHEN,
}

COLLECTION_TYPE = {
    "residual": "Residual Waste",
    "recycling": "Recycling",
    "garden": "Garden Waste",
    "food": "Food Waste",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def _get_collective_key(self, session_key: str, session: requests.Session) -> str:
        result = run_lookup(
            session,
            API_URL,
            session_key,
            AUTHENTICATOR_LOOKUP_ID,
            {"Section 1": {}},
        )
        rows_data = result["integration"]["transformed"]["rows_data"]
        first_row = next(iter(rows_data.values())) if rows_data else {}
        return first_row["collectiveKey"]

    def get_collections(
        self, session_key: str, session: requests.Session
    ) -> list[Collection]:
        collective_key = self._get_collective_key(session_key, session)

        start = datetime.now()
        end = start + timedelta(days=LOOKAHEAD_DAYS)
        result = run_lookup(
            session,
            API_URL,
            session_key,
            COLLECTION_DAYS_LOOKUP_ID,
            {
                "Section 1": {
                    "collectiveUPRN": {"value": self._uprn},
                    "collectiveKey": {"value": collective_key},
                    "collectiveGetJobStartDate": {
                        "value": start.strftime("%Y-%m-%dT00:00:00")
                    },
                    "collectiveGetJobEndDate": {
                        "value": end.strftime("%Y-%m-%dT00:00:00")
                    },
                }
            },
        )
        rows_data = result["integration"]["transformed"]["rows_data"]
        return (
            list(rows_data.values()) if isinstance(rows_data, dict) else list(rows_data)
        )

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session_key = init_session(
            session,
            INITIAL_URL,
            AUTH_URL,
            HOSTNAME,
            auth_test_url=AUTH_TEST,
        )
        collections = self.get_collections(session_key, session)

        entries = []
        for collection in collections:
            date_string = collection["collectiveCollectionDate"]
            date = datetime.strptime(date_string, "%d/%m/%Y").date()
            waste_type = collection["collectiveWasteType"].lower()
            service = next((key for key in COLLECTION_TYPE if key in waste_type), None)
            icon = ICON_MAP.get(service)
            collection_type = (
                COLLECTION_TYPE[service]
                if service is not None
                else collection["collectiveWasteType"]
            )
            entries.append(Collection(date=date, t=collection_type, icon=icon))

        return entries
