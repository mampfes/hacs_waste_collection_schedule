from typing import TypedDict

import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Elmbridge Borough Council"
DESCRIPTION = "Source for waste collection services for Elmbridge Borough Council"
URL = "https://www.elmbridge.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": 10013119164},
    "Test_002": {"uprn": "100061309206"},
    "Test_003": {"uprn": 100062119825},
    "Test_004": {"uprn": "100061343923"},
    "Test_005": {"uprn": 100062372553},
}


BASE_URL = "https://elmbridge-self.achieveservice.com"
INTIAL_URL = f"{BASE_URL}/service/Your_bin_collection_days"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/elmbridge-self.achieveservice.com"
API_URL = f"{BASE_URL}/apibroker/runLookup"


ICON_MAP = {
    "Domestic Waste": "mdi:trash-can",
    "Domestic Recycling": "mdi:recycle",
    "Food Waste": "mdi:food",
    "Textiles and Small WEEE": "mdi:tshirt-crew",
}


class CollectionResult(TypedDict):
    Date: str
    Service1: str
    Service2: str
    Service3: str


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def get_collections(self, session_key: str, session: requests.Session) -> list[Collection]:
        result = run_lookup(
            session,
            API_URL,
            session_key,
            "663b557cdaece",
            {"Section 1": {"UPRN": {"value": self._uprn}}},
        )
        return list(result["integration"]["transformed"]["rows_data"].values())

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session_key = init_session(
            session,
            INTIAL_URL,
            AUTH_URL,
            "elmbridge-self.achieveservice.com",
            auth_test_url=AUTH_TEST,
        )
        collections = self.get_collections(session_key, session)

        entries = []
        for collection in collections:
            date = parse(collection["Date"], dayfirst=True).date()
            for service in [
                collection["Service1"],
                collection["Service2"],
                collection["Service3"],
            ]:
                if not service:
                    continue
                service = service.removesuffix(" Collection Service")
                icon = ICON_MAP.get(service)
                entries.append(Collection(date=date, t=service, icon=icon))

        return entries
