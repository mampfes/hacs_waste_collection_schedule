import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Hässleholm Miljö"
DESCRIPTION = "Source for waste collection schedules from Hässleholm Miljö, Sweden."
URL = "https://hassleholmmiljo.se"

TEST_CASES = {
    "Tyringevägen 24, Finja": {"alias": "hmab-tyringevaegen-24-finja"},
}

ICON_MAP = {
    "Kärl1": "mdi:trash-can",
    "Kärl2": "mdi:recycle",
    "Trädgårdsavfall": "mdi:leaf",
    "Budad hämtning": "mdi:truck",
}

BASE_URL = "https://hassleholmmiljo.se/privat/sophamtning/tomningskalender"
API_URL = (
    "https://api-universal.appbolaget.se/@universal/waste/properties/{property_id}/"
)

TIMEZONE = ZoneInfo("Europe/Stockholm")


class Source:
    def __init__(self, alias: str):
        self._alias = alias

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        # Step 1: Fetch the calendar page to extract property_id and unit UUID
        resp = session.get(BASE_URL, params={"alias": self._alias}, timeout=30)
        resp.raise_for_status()

        property_id, unit_uuid = self._extract_ids(resp.text)

        if not property_id or not unit_uuid:
            raise SourceArgumentNotFound(
                "alias",
                self._alias,
            )

        # Step 2: Fetch the full collection schedule from the Appbolaget API
        api_resp = session.get(
            API_URL.format(property_id=property_id),
            params={"unit": unit_uuid},
            timeout=30,
        )
        api_resp.raise_for_status()

        data = api_resp.json()
        if data.get("status") != 200:
            raise SourceArgumentNotFound(
                "alias",
                self._alias,
            )

        return self._parse_collections(data["data"])

    def _extract_ids(self, html: str) -> tuple[str | None, str | None]:
        """Extract property_id and unit UUID from the embedded page state."""
        # Find the calendarMonth state block
        scripts = re.findall(
            r"AppRegistry\.registerInitialState\([^,]+,(\{.*?\})\);",
            html,
            re.DOTALL,
        )

        for script in scripts:
            try:
                state = json.loads(script)
            except (json.JSONDecodeError, ValueError):
                continue

            cm = state.get("calendarMonth")
            if not cm:
                continue

            property_id = cm.get("property") or (
                cm.get("customers", [None])[0] if cm.get("customers") else None
            )
            pdf_url = cm.get("pdfUrl", "")
            unit_match = re.search(r"unit=([0-9a-f-]{36})", pdf_url)
            unit_uuid = unit_match.group(1) if unit_match else None

            if property_id and unit_uuid:
                return property_id, unit_uuid

        return None, None

    def _parse_collections(self, data: dict) -> list[Collection]:
        """Parse service collections from the Appbolaget API response."""
        entries: list[Collection] = []

        for service in data.get("services", []):
            code = service.get("code", {})
            waste_type = code.get("description") or code.get("code", "Unknown")
            icon = ICON_MAP.get(waste_type)

            for collection in service.get("collections", []):
                collection_at = collection.get("collection_at")
                if not collection_at:
                    continue

                # Dates are stored in UTC; convert to local Stockholm date
                dt_utc = datetime.fromisoformat(collection_at).replace(
                    tzinfo=timezone.utc
                )
                dt_local = dt_utc.astimezone(TIMEZONE)
                date = dt_local.date()

                entries.append(Collection(date=date, t=waste_type, icon=icon))

        return entries
