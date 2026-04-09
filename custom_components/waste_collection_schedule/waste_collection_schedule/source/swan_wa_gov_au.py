import requests
from dateutil.parser import parse as dateparse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "City of Swan"
DESCRIPTION = "Source for City of Swan waste collection."
URL = "https://www.swan.wa.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "Stratton": {"address": "34 Oldenburg Pass Stratton"},
    "Midland": {"address": "307 Great Eastern Highway Midland"},
}

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '34 Oldenburg Pass Stratton'). "
    "Search at https://www.swan.wa.gov.au/waste-and-sustainability/waste-and-recycling-services/bins/find-my-bin-day",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '34 Oldenburg Pass Stratton')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

BASE_URL = "https://swan.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine"
CONFIG_ID = "4c6eefa0-c035-40d1-b553-be6e06446b38"
PROJECT_ID = "41a8ffbd-0da0-47c9-9957-b0dcb8a1bfc3"
MODULE_ID = "5a0205e5-ab05-4d94-a97f-2ae565ae48ff"
SEARCH_FORM = "7f2d1f72-efe2-4527-9fcc-1e2ba8348e64"
SEL_LAYER = "efd1a218-d9c4-43ec-b1bb-17514d03c3a3"


class Source:
    def __init__(self, address: str):
        if not address:
            raise SourceArgumentRequired("address", "A street address is required")
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Step 1: Create IntraMaps session
        r = s.get(
            f"{BASE_URL}/Projects/",
            params={
                "configId": CONFIG_ID,
                "appType": "MapBuilder",
                "project": PROJECT_ID,
                "datasetCode": "",
            },
        )
        r.raise_for_status()
        session_id = r.headers.get("X-IntraMaps-Session")

        # Step 2: Initialize module
        r = s.post(
            f"{BASE_URL}/Modules/",
            params={"IntraMapsSession": session_id},
            json={
                "module": MODULE_ID,
                "includeBasemaps": False,
                "includeWktInSelection": True,
            },
            headers=headers,
        )
        r.raise_for_status()

        # Step 3: Search for address
        r = s.post(
            f"{BASE_URL}/Search/",
            params={
                "infoPanelWidth": "-350",
                "mode": "Refresh",
                "form": SEARCH_FORM,
                "resubmit": "false",
                "selectionLayersFilter": SEL_LAYER,
                "IntraMapsSession": session_id,
            },
            json={"fields": [self._address]},
            headers=headers,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("fullText", [])

        if not results:
            raise SourceArgumentNotFound("address", self._address)

        if len(results) > 1:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                [r["displayValue"] for r in results[:20]],
            )

        result = results[0]

        # Step 4: Get waste collection info
        r = s.post(
            f"{BASE_URL}/Search/Refine/Set",
            params={"IntraMapsSession": session_id},
            json={
                "selectionLayer": result["selectionLayer"],
                "mapKey": result["mapKey"],
                "dbKey": result["dbKey"],
                "infoPanelWidth": "-350",
            },
            headers=headers,
        )
        r.raise_for_status()
        rdata = r.json()

        panel_fields = (
            rdata.get("infoPanels", {})
            .get("info1", {})
            .get("feature", {})
            .get("fields", [])
        )

        # Parse collection fields
        field_map = {}
        for field in panel_fields:
            if field.get("type") != "Text":
                continue
            caption = field.get("caption", "")
            value = field.get("value", {})
            if isinstance(value, dict):
                field_map[caption] = value.get("value", "")

        entries: list[Collection] = []

        # General Waste — fortnightly from next date
        self._add_fortnightly(
            entries, field_map.get("Next General Waste Collection", ""), "General Waste"
        )

        # Recycling — fortnightly from next date
        self._add_fortnightly(
            entries, field_map.get("Next Recycling Collection", ""), "Recycling"
        )

        # FOGO — may be a date or a status message
        fogo_val = field_map.get("Next FOGO Collection", "")
        self._add_fortnightly(entries, fogo_val, "FOGO")

        return entries

    @staticmethod
    def _add_fortnightly(
        entries: list[Collection], date_str: str, waste_type: str
    ) -> None:
        if not date_str:
            return
        try:
            next_date = dateparse(date_str, dayfirst=True).date()
        except (ValueError, TypeError):
            return

        for d in rrule(WEEKLY, interval=2, dtstart=next_date, count=13):
            entries.append(
                Collection(date=d.date(), t=waste_type, icon=ICON_MAP.get(waste_type))
            )
