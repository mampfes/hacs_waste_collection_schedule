# Credit where it's due:
# This is based on the elmbridge_gov_uk source


from datetime import datetime

import requests
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

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

    def get_collections(self, session_key: str, session: requests.Session) -> list[Collection]:
        result = run_lookup(
            session,
            API_URL,
            session_key,
            LOOKUP_ID,
            self._get_payload(),
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
