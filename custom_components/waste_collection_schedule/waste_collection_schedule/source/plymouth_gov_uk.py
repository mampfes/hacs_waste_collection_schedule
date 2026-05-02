from datetime import datetime

import requests
from waste_collection_schedule import Collection
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

FORM_ID = "5c99439d85f83"
HOSTNAME = "plymouth-self.achieveservice.com"
BASE_URL = f"https://{HOSTNAME}"
INITIAL_URL = f"{BASE_URL}/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-31283f9a-3ae7-4225-af71-bf3884e0ac1b/AF-Stagedba4a7d5-e916-46b6-abdb-643d38bec875/definition.json&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/{HOSTNAME}"
API_URL = f"{BASE_URL}/apibroker/runLookup"

ICON_MAP = {
    "DO": "mdi:trash-can",
    "RE": "mdi:recycle",
}

COLLECTION_TYPE = {
    "DO": "Domestic Brown Bin",
    "RE": "Recycling Green Bin",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def get_collections(self, session_key: str, session: requests.Session) -> list[Collection]:
        result = run_lookup(
            session,
            API_URL,
            session_key,
            FORM_ID,
            {
                "Section 1": {
                    "number1": {"value": self._uprn},
                    "nextncoll": {"value": "9"},
                }
            },
        )
        return list(result["integration"]["transformed"]["rows_data"].values())

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
            date_string = collection["Date"]
            date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S").date()
            service = collection["Round_Type"]
            icon = ICON_MAP.get(service)
            collection_type = COLLECTION_TYPE[service]
            entries.append(Collection(date=date, t=collection_type, icon=icon))

        return entries
