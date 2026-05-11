import datetime
import time

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.AchieveForms import init_session

TITLE = "Spelthorne Borough Council"
DESCRIPTION = "Source for Spelthorne Borough Council, Surrey, UK."
URL = "https://www.spelthorne.gov.uk"
TEST_CASES = {
    "241 Thames Side Chertsey": {"uprn": "33042469"},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://spelthorne-self.achieveservice.com/service/Waste_Collections "
        "and searching for your address. Your UPRN can also be found at "
        "https://www.findmyaddress.co.uk/."
    )
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}

BASE_URL = "https://spelthorne-self.achieveservice.com"
SERVICE_URL = f"{BASE_URL}/service/Waste_Collections"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST_URL = f"{BASE_URL}/apibroker/domain/spelthorne-self.achieveservice.com"
API_URL = f"{BASE_URL}/apibroker/runLookup"
HOSTNAME = "spelthorne-self.achieveservice.com"

TOKEN_LOOKUP_ID = "5f97e6e09fedd"
COLLECTION_LOOKUP_ID = "66042a164c9a5"

ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

_WASTE_FIELDS = [
    ("GwPrevCollection", "GwNextCollection", "Garden Waste"),
    ("RefPrevCollection", "RefNextCollection", "Refuse"),
    ("RecPrevCollection", "RecNextCollection", "Recycling"),
]


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        sid = init_session(
            session,
            SERVICE_URL,
            AUTH_URL,
            HOSTNAME,
            auth_test_url=AUTH_TEST_URL,
        )

        csrf_resp = session.get(
            f"{BASE_URL}/api/nextref", params={"sid": sid}, timeout=30
        )
        csrf_resp.raise_for_status()
        csrf = csrf_resp.json()["data"]["csrfToken"]

        # Spelthorne requires a server-generated one-time token fetched before lookup
        tok_resp = session.get(
            API_URL,
            params={
                "id": TOKEN_LOOKUP_ID,
                "repeat_against": "",
                "noRetry": "true",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AF-Renderer::Self",
                "_": int(time.time() * 1000),
                "sid": sid,
            },
            timeout=30,
        )
        tok_resp.raise_for_status()
        token_string = (
            tok_resp.json()
            .get("integration", {})
            .get("transformed", {})
            .get("rows_data", {})
            .get("0", {})
            .get("tokenString", "")
        )
        if not token_string:
            raise ValueError(
                "Failed to retrieve authentication token from Spelthorne API"
            )

        today = datetime.date.today()
        last2weeks = (today - datetime.timedelta(days=14)).isoformat()
        end_date = (today + datetime.timedelta(days=90)).isoformat()

        resp = session.post(
            API_URL,
            params={
                "id": COLLECTION_LOOKUP_ID,
                "repeat_against": "",
                "noRetry": "true",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AF-Renderer::Self",
                "_": int(time.time() * 1000),
                "sid": sid,
            },
            json={
                "formValues": {
                    "Property details": {
                        "token": {"value": token_string},
                        "uprn1": {"value": self._uprn},
                        "last2Weeks": {"value": last2weeks},
                        "endDate": {"value": end_date},
                    }
                }
            },
            headers={"X-CSRF-Token": csrf},
            timeout=30,
        )
        resp.raise_for_status()

        row = (
            resp.json()
            .get("integration", {})
            .get("transformed", {})
            .get("rows_data", {})
            .get("0", {})
        )

        if row.get("NoRecordMessage", "").strip():
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []
        for prev_field, next_field, waste_type in _WASTE_FIELDS:
            for date_str in (row.get(prev_field, ""), row.get(next_field, "")):
                date_str = date_str.strip()
                if not date_str:
                    continue
                try:
                    collection_date = datetime.date.fromisoformat(date_str)
                except ValueError:
                    continue
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
