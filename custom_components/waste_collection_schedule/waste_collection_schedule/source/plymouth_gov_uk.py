from datetime import datetime
from typing import TypedDict

import requests
from waste_collection_schedule import Collection

TITLE = "Plymouth City Council"
DESCRIPTION = "Source for waste collection services for Plymouth City Council"
URL = "https://www.plymouth.gov.uk/"

TEST_CASES = {
    "Test_001": {"uprn": 100040429524 },
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
        self._session = requests.Session()

    def _init_session(self) -> str:
        self._session = requests.Session()
        
        r = self._session.get(INITIAL_URL)
        r.raise_for_status()

        params: dict[str, str | int] = {
            "uri": r.url,
            "hostname": HOSTNAME,
            "withCredentials": "true",
        }
        r = self._session.get(AUTH_URL, params=params)
        r.raise_for_status()

        data = r.json()
        session_key = data["auth-session"]
        params = {
            "sid": session_key,
            "_": int(datetime.now().timestamp() * 1000),
        }
        r = self._session.get(AUTH_TEST, params=params)
        r.raise_for_status()

        return session_key

    def get_collections(self, session_key: str) -> list[Collection]:
        params: dict[str, int | str] = {
            "id": FORM_ID,
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": int(datetime.now().timestamp() * 1000),
            "sid": session_key,
        }

        payload = {
            "formValues": {
                "Section 1": {
                    "number1": {
                        "value": self._uprn
                    },
                    "nextncoll": {
                        "value": "9"
                    }
                }
            }
        }

        r = self._session.post(API_URL, params=params, json=payload)
        r.raise_for_status()
        return list(r.json()["integration"]["transformed"]["rows_data"].values())

    def fetch(self) -> list[Collection]:
        session_key = self._init_session()
        collections = self.get_collections(session_key)

        entries = []
        for collection in collections:
            date_string = collection["Date"]
            date = datetime.strptime(date_string,"%Y-%m-%dT%H:%M:%S").date()
            service = collection["Round_Type"]
            icon = ICON_MAP.get(service)
            collection_type = COLLECTION_TYPE[service]
            entries.append(Collection(date=date, t=collection_type, icon=icon))

        return entries