from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Epping Forest District Council"
DESCRIPTION = "Source for Epping Forest District Council, Essex, UK."
URL = "https://www.eppingforestdc.gov.uk"
TEST_CASES = {
    "51 Crows Road Epping": {"uprn": "100090495060"},
    "47 Crows Road Epping": {"uprn": 100090495056},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://eppingforestdc-self.achieveservice.com/service/Check_your_collection_day "
        "and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/."
    )
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}

BASE_URL = "https://eppingforestdc-self.achieveservice.com"
SERVICE_URL = f"{BASE_URL}/en/service/Check_your_collection_day"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
API_URL = f"{BASE_URL}/apibroker/runLookup"

LOOKUP_COLLECTIONS = "6651dfb99a74d"

ICON_MAP = {
    "food": "mdi:food",
    "garden": "mdi:leaf",
    "recycling": "mdi:recycle",
    "refuse": "mdi:trash-can",
    "general": "mdi:trash-can",
    "clinical": "mdi:medical-bag",
}

SERVICES = [
    ("FoodWaste", "FoodWasteServiceName", "FoodWasteServiceNextCollection"),
    ("FoodGarden", "FoodGardenServiceName", "FoodGardenServiceNextCollection"),
    ("GardenWaste", "GardenWasteServiceName", "GardenWasteServiceNextCollection"),
    ("Recycling", "RecyclingServiceName", "RecyclingServiceNextCollection"),
    ("GeneralWaste", "GeneralWasteServiceName", "GeneralWasteServiceNextCollection"),
]


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        sid = init_session(
            session,
            SERVICE_URL,
            AUTH_URL,
            "eppingforestdc-self.achieveservice.com",
        )
        result = run_lookup(
            session,
            API_URL,
            sid,
            LOOKUP_COLLECTIONS,
            {"Address": {"LookupUPRN": {"value": self._uprn}}},
        )

        rows = (
            result.get("integration", {}).get("transformed", {}).get("rows_data", {})
        )
        row = rows.get("0", {})

        entries = []
        for _key, name_field, date_field in SERVICES:
            service_name = row.get(name_field, "")
            date_str = row.get(date_field, "")
            if not service_name or not date_str:
                continue
            try:
                collection_date = datetime.fromisoformat(date_str[:10]).date()
            except ValueError:
                continue
            # Skip sentinel date returned when service has no next collection
            if collection_date.year < 2000:
                continue
            entries.append(
                Collection(
                    date=collection_date,
                    t=service_name,
                    icon=self._get_icon(service_name),
                )
            )

        if not entries:
            raise SourceArgumentNotFound("uprn", self._uprn)

        return entries

    def _get_icon(self, service_name: str) -> str | None:
        lower = service_name.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None
