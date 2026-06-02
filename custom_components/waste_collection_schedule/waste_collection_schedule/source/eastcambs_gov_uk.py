import datetime
import re
import time

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "East Cambridgeshire District Council"
DESCRIPTION = "Source for eastcambs.gov.uk, East Cambridgeshire District Council, UK"
URL = "https://www.eastcambs.gov.uk"
TEST_CASES = {
    "14 Meadow Way Ely": {"uprn": 10002601730},
    "20 Forehill Ely": {"uprn": "10002597181"},
}

COUNTRY = "uk"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://eastcambs-self.achieveservice.com/service/Check_your_waste_collection_day "
        "and searching for your address. Your UPRN can also be found at https://www.findmyaddress.co.uk/."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number",
    }
}

HOSTNAME = "eastcambs-self.achieveservice.com"
PROCESS_ID = "2c7575a6-0139-4555-9d8a-ab504a44d989"
STAGE_ID = "94ee5097-94db-474d-bc7a-d1796e3ab83a"
INITIAL_URL = f"https://{HOSTNAME}/AchieveForms/"
AUTH_LOOKUP_ID = "69d8f92eea3cf"
COLLECTIONS_LOOKUP_ID = "6784e74793b68"
API_URL = f"https://{HOSTNAME}/apibroker/runLookup"

ICON_MAP = {
    "RECYCLING BIN": Icons.RECYCLING,
    "OUTDOOR FOOD CADDY": Icons.BIO_KITCHEN,
    "INDOOR FOOD CADDY": Icons.BIO_KITCHEN,
    "RUBBISH BIN": Icons.GENERAL_WASTE,
    "GARDEN WASTE BIN": Icons.GARDEN,
    "BROWN BAGS": Icons.GENERAL_WASTE,
    "PURPLE BAGS": Icons.RECYCLING,
    "CLEAR BAGS": Icons.RECYCLING,
    "BLACK BAG": Icons.GENERAL_WASTE,
    "BLUE BIN": Icons.RECYCLING,
    "GREEN": Icons.GARDEN,
}


def _get_icon(collection_type: str) -> str | None:
    upper = collection_type.upper()
    for key, icon in ICON_MAP.items():
        if key in upper:
            return icon
    return None


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"user-agent": "Mozilla/5.0"})

        # Step 1: Load the AchieveForms page to get a session
        r = session.get(
            INITIAL_URL,
            params={
                "mode": "fill",
                "consentMessage": "yes",
                "form_uri": f"sandbox-publish://AF-Process-{PROCESS_ID}/AF-Stage-{STAGE_ID}/definition.json",
                "process": "1",
                "process_uri": f"sandbox-processes://AF-Process-{PROCESS_ID}",
                "process_id": f"AF-Process-{PROCESS_ID}",
            },
            timeout=30,
        )
        r.raise_for_status()

        sid_match = re.search(r'"auth-session":"([^"]+)"', r.text)
        if not sid_match:
            raise ValueError("Could not obtain session ID from East Cambs service")
        sid = sid_match.group(1)

        # Step 2: Obtain authentication token
        timestamp = int(time.time() * 1000)
        r_auth = session.post(
            API_URL,
            params={
                "id": AUTH_LOOKUP_ID,
                "repeat_against": "",
                "noRetry": "false",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AchieveForms",
                "_": timestamp,
                "sid": sid,
            },
            json={"formValues": {"Section 1": {}}},
            timeout=30,
        )
        r_auth.raise_for_status()
        auth_data = r_auth.json()
        auth_token = (
            auth_data.get("integration", {})
            .get("transformed", {})
            .get("rows_data", {})
            .get("0", {})
            .get("AuthenticateResponse", "")
        )

        # Step 3: Fetch upcoming bin collections
        today = datetime.date.today()
        # The new service started June 1 2026; use that as the earliest start date
        service_start = datetime.date(2026, 6, 1)
        start_date = max(today, service_start)
        end_date = today + datetime.timedelta(days=90)

        timestamp = int(time.time() * 1000)
        r_col = session.post(
            API_URL,
            params={
                "id": COLLECTIONS_LOOKUP_ID,
                "repeat_against": "",
                "noRetry": "false",
                "getOnlyTokens": "undefined",
                "log_id": "",
                "app_name": "AchieveForms",
                "_": timestamp,
                "sid": sid,
            },
            json={
                "formValues": {
                    "Section 1": {
                        "AuthenticateResponse": {"value": auth_token},
                        "selected_uprn": {"value": self._uprn},
                        "MinimumDateForNextDates": {
                            "value": start_date.strftime("%Y-%m-%d")
                        },
                        "MaximumDateFormattedNext": {
                            "value": end_date.strftime("%Y-%m-%d")
                        },
                    }
                }
            },
            timeout=30,
        )
        r_col.raise_for_status()
        col_data = r_col.json()

        # select_data contains all collection occurrences in chronological order
        # Each entry: {"label": "BIN TYPE - DD/MM/YYYY", "value": "BIN TYPE"}
        select_data = (
            col_data.get("integration", {})
            .get("transformed", {})
            .get("select_data", [])
        )

        if not select_data:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries: list[Collection] = []
        for item in select_data:
            label = item.get("label", "")
            # Label format: "BIN TYPE - DD/MM/YYYY"
            parts = label.rsplit(" - ", 1)
            if len(parts) != 2:
                continue
            bin_type, date_str = parts
            try:
                collection_date = datetime.datetime.strptime(
                    date_str, "%d/%m/%Y"
                ).date()
            except ValueError:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=bin_type.strip(),
                    icon=_get_icon(bin_type.strip()),
                )
            )

        return entries
