import datetime
import time

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Midlothian Council"
DESCRIPTION = "Source script for my.midlothian.gov.uk bin collections"
URL = "https://my.midlothian.gov.uk/"
LOOKUP_ID_BIN_COLLECTION_SERVICE = "69948bdca6012"
NO_RETRY = "false"
TEST_CASES = {
    "Test1": {"uprn": "120001401", "postcode": "EH26 8AG"},
}

AUTH_URL = "https://my.midlothian.gov.uk/authapi/isauthenticated"
DOMAIN_URL = "https://my.midlothian.gov.uk/apibroker/domain/my.midlothian.gov.uk"
RUN_LOOKUP_URL = "https://my.midlothian.gov.uk/apibroker/runLookup"

ICON_MAP = {
    "Food Collection Service": "mdi:food-apple",
    "Glass Collection Service": "mdi:glass-fragile",
    "Residual Collection Service": "mdi:trash-can",
    "Garden Collection Service": "mdi:leaf",
    "Recycling Collection Service": "mdi:recycle",
    "Card Collection Service": "mdi:archive",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your UPRN and postcode from your council documents or invoices.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (required)",
        "postcode": "Postcode of the property (required)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "UPRN",
        "postcode": "Postcode",
    },
}


class Source:
    def __init__(self, uprn: str, postcode: str):
        self._uprn = uprn
        self._postcode = postcode

    def fetch(self):
        session = requests.Session()
        auth_resp = session.get(AUTH_URL, timeout=30)
        auth_resp.raise_for_status()
        try:
            auth_data = auth_resp.json()
        except ValueError as err:
            raise SourceArgumentException(
                "uprn", f"Invalid response while creating session: {err}"
            ) from err

        sid = auth_data.get("auth-session")
        if not sid:
            raise SourceArgumentException(
                "uprn", "Could not establish session with council form."
            )

        timestamp = time.time_ns() // 1_000_000
        domain_resp = session.get(
            DOMAIN_URL, params={"_": timestamp, "sid": sid}, timeout=30
        )
        domain_resp.raise_for_status()

        # Step 2: Prepare runLookup request with required params
        today = datetime.date.today()
        from_date = today.strftime("%Y-%m-%d")
        # Use timedelta to avoid leap-day crashes from date.replace(year=+1).
        to_date = (today + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        payload = {
            "stopOnFailure": True,
            "usePHPIntegrations": True,
            "stage_id": "AF-Stage-a0bdbc4e-b9fc-46f0-bb0c-14a12cd927ed",
            "stage_name": "Stage 1",
            "formId": "AF-Form-033371a6-b0e4-4e16-a3b5-f68f592d8bf1",
            "formValues": {
                "Section 1": {
                    "postcode": {"value": self._postcode},
                    "UPRN": {"value": self._uprn},
                    "uprn": {"value": self._uprn},
                    "fromDate": {"value": from_date},
                    "toDate": {"value": to_date},
                }
            },
        }
        params = {
            "id": LOOKUP_ID_BIN_COLLECTION_SERVICE,
            "repeat_against": "",
            "noRetry": NO_RETRY,
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": time.time_ns() // 1_000_000,
            "sid": sid,
        }
        resp = session.post(RUN_LOOKUP_URL, params=params, json=payload, timeout=30)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError as err:
            raise SourceArgumentException(
                "uprn", f"Council lookup returned invalid JSON: {err}"
            ) from err

        if data.get("result") == "logout":
            raise SourceArgumentException(
                "uprn", "Session expired while querying collection data."
            )
        rows = data.get("integration", {}).get("transformed", {}).get("rows_data", {})
        if not rows:
            raise SourceArgumentNotFound(
                "uprn", self._uprn, "No collection data returned for this address."
            )

        entries = []
        failed_rows = []
        for row in rows.values():
            date_str = row.get("Date") or row.get("date")
            try:
                date = datetime.datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S").date()
            except (ValueError, TypeError, AttributeError) as e:
                # Track parsing failures - expected exceptions for invalid/missing dates
                failed_rows.append(f"Date='{date_str}': {type(e).__name__}")
                continue
            waste_type = row.get("Service") or row.get("service")
            entries.append(
                Collection(
                    date=date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        # If we got rows but couldn't parse any, the format likely changed
        if rows and not entries:
            raise SourceArgumentException(
                "uprn",
                f"Failed to parse any collection dates from {len(rows)} rows. "
                f"API format may have changed. Failures: {failed_rows[:3]}",
            )

        return entries
