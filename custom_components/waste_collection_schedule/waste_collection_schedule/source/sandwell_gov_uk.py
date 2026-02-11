from __future__ import annotations

from waste_collection_schedule import Collection
from datetime import datetime, timedelta
from typing import Any

import requests
import time

TITLE = "Sandwell Council"
DESCRIPTION = "Bin collection dates via my.sandwell.gov.uk (APIBroker runLookup)"
URL = "https://my.sandwell.gov.uk/"
COUNTRY = "uk"

# Must be a dict for the test script (it calls .items()) and must pass kwargs directly to Source(...)
TEST_CASES = {
    "uprn_10008535856": {"uprn": "10008535856"},
    "uprn_10008535857": {"uprn": "10008535857"},
}

# Endpoints + headers (mirrors the working integration you found)
SESSION_URL = (
    "https://my.sandwell.gov.uk/authapi/isauthenticated?"
    "uri=https://my.sandwell.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-ebaa26a2-393c-4a3c-84f5-e61564192a8a/AF-Stage-e4c2cb32-db55-4ff5-845c-8b27f87346c4/definition.json&redirectlink=/en&cancelRedirectLink=/en&consentMessage=yes"
)
API_URL = "https://my.sandwell.gov.uk/apibroker/runLookup"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://my.sandwell.gov.uk/fillform/?iframe_id=fillform-frame-1&db_id=",
}

# lookup_id, date_field_in_response, waste_type_label
LOOKUPS = [
    ("686294de50729", "DWDate", "Household Waste (Grey)"),
    ("68629dd642423", "MDRDate", "Recycling (Blue)"),
    ("6863a78a1dd8e", "FWDate", "Food Waste (Brown)"),
    ("686295a88a750", "GWDate", "Garden Waste (Green)"),  # may be unsubscribed => empty rows
]

ICON_MAP = {
    "Garden Waste (Green)": "mdi:leaf",
    "Household Waste (Grey)": "mdi:trash-can",
    "Food Waste (Brown)": "mdi:food-apple",
    "Recycling (Blue)": "mdi:recycle",
}

def _parse_date(d: str) -> datetime.date:
    # Sandwell returns dd/mm/YYYY
    try:
        return datetime.strptime(d, "%d/%m/%Y").date()
    except Exception as e:
        raise ValueError(f"Invalid date from Sandwell: {d}") from e


class Source:
    def __init__(self, uprn: str):
        if not uprn or not uprn.isdigit():
            raise ValueError("uprn must be a numeric string")
        self._uprn = uprn

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []

        session = requests.Session()

        # 1) Get session id (sid)
        r = session.get(SESSION_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        session_data = r.json()

        sid = session_data.get("auth-session")
        if not sid:
            raise ValueError(f"Unexpected auth response (no auth-session): {session_data}")

        # 2) Prepare common payload + params
        payload: dict[str, Any] = {
            "formValues": {
                "Property details": {
                    "Uprn": {"value": self._uprn},
                    "NextCollectionFromDate": {"value": datetime.today().strftime("%Y-%m-%d")},
                }
            }
        }

        base_params = {
            "repeat_against": "",
            "noRetry": "false",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "sid": sid,
            "_": str(int(time.time() * 1000)),  # timestamp
        }

        # 3) Call each lookup id and convert rows -> Collection entries
        for lookup_id, date_key, waste_type in LOOKUPS:
            params = {"id": lookup_id, **base_params}

            resp = session.post(API_URL, json=payload, headers=HEADERS, params=params, timeout=30)

            # If Sandwell decides you're not authorised, you'll often see {"result":"logout"}
            # which can still be HTTP 200, so check JSON too.
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict) and data.get("result") == "logout":
                raise PermissionError("Sandwell returned logout (session rejected). Try again later or adjust headers.")

            transformed = (data.get("integration") or {}).get("transformed") or {}
            rows_data = transformed.get("rows_data")

            # Garden waste unsubscribed (and sometimes others) => rows_data may be [] or missing
            if not isinstance(rows_data, dict):
                continue

            for row in rows_data.values():
                d = row.get(date_key)
                if not d:
                    continue
                entries.append(
                    Collection(
                        date=_parse_date(d),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can-outline")
                    )
                )

        return entries
