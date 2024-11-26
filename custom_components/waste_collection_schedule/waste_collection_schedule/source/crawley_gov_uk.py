# Credit where it's due:
# This is based on the elmbridge_gov_uk source


from datetime import datetime

import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Crawley Borough Council (myCrawley)"
DESCRIPTION = "Source for Crawley Borough Council (myCrawley)."
URL = "https://crawley.gov.uk/"
TEST_CASES = {
    "Feroners Cl": {"uprn": "100061775179"},
    "Peterborough Road": {"uprn": 100061787552, "usrn": 9700731},
}


ICON_MAP = {
    "Rubbish and Small Electricals Collection": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "GREENbin Garden Waste Collection": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycling and Textiles Collection": "mdi:recycle",
}


BASE_URL = "https://my.crawley.gov.uk"
INTIAL_URL = f"{BASE_URL}/en/service/check_my_bin_collection"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
AUTH_TEST = f"{BASE_URL}/apibroker/domain/my.crawley.gov.uk"
API_URL = f"{BASE_URL}/apibroker/runLookup"

LOOKUP_ID = "5b4f0ec5f13f4"


class Source:
    def __init__(self, uprn: str | int, usrn: str | int | None = None):
        self._uprn = str(uprn)
        self._usrn = str(usrn) if usrn else None

    def _get_payload(self) -> dict[str, dict]:
        now = datetime.now()
        return {
            "formValues": {
                "Address": {
                    "address": {
                        "value": {
                            "Address": {
                                "usrn": {"value": self._usrn or "0000"},
                                "uprn": {"value": self._uprn},
                            }
                        }
                    },
                    "dayConverted": {"value": now.strftime("%d/%m/%Y")},
                    "getCollection": {"value": "true"},
                    "getWorksheets": {"value": "false"},
                }
            }
        }

    def _init_session(self) -> str:
        self._session = requests.Session()
        r = self._session.get(INTIAL_URL)
        r.raise_for_status()
        params: dict[str, str | int] = {
            "uri": r.url,
            "hostname": "elmbridge-self.achieveservice.com",
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
            "id": LOOKUP_ID,
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": int(datetime.now().timestamp() * 1000),
            "sid": session_key,
        }
        payload = self._get_payload()
        r = self._session.post(API_URL, params=params, json=payload)
        r.raise_for_status()
        return list(r.json()["integration"]["transformed"]["rows_data"].values())

    def fetch(self) -> list[Collection]:
        session_key = self._init_session()
        collections = self.get_collections(session_key)
        date_parse_failed = []
        entries = []
        for collection in collections:
            for key in [
                k
                for k in collection.keys()
                if k.endswith("DateCurrent") or k.endswith("DateNext")
            ]:
                date_str = collection[key]
                try:
                    date = parse(date_str, dayfirst=True).date()
                except ValueError:
                    date_parse_failed.append(date_str)
                if not date_str:
                    continue
                bin_type = key.split("Date")[0]
                icon = ICON_MAP.get(bin_type)
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        if not entries:
            if date_parse_failed:
                raise ValueError(
                    f"Failed to parse dates: {', '.join(date_parse_failed)}"
                )
            raise ValueError(f"No collections found for {self._uprn}")
        return entries
