import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Telge Återvinning"
DESCRIPTION = "Source for Telge Återvinning, household waste collection in Södertälje municipality"
URL = "https://www.telge.se"
COUNTRY = "se"
API_URL = "https://www.telge.se/api/thorweb/garbagecollection"
TEST_CASES = {
    "Residential Södertälje": {"address": "BERGSGATAN 22, SÖDERTÄLJE"},
    "Rural with latrine": {"address": "BERGA 1, JÄRNA"},
    "Garden waste": {"address": "PALLSTIGEN 1, HÖLÖ"},
    "Commercial sorting": {"address": "STORGATAN 13 VÅRDCENTRAL JÄRNA, JÄRNA"},
    "Septic tank": {"address": "BACKA 3 MARIELUND, JÄRNA"},
}

ICON_MAP = {
    "BRÄNN": "mdi:fire",
    "GLOF": "mdi:bottle-wine-outline",
    "HEMSORT": "mdi:recycle",
    "HUSHSORT": "mdi:trash-can",
    "LATRIN": "mdi:toilet",
    "MATAVF": "mdi:food-apple",
    "METFÖRP": "mdi:can",
    "PLASTFÖRP": "mdi:bottle-soda-outline",
    "RETURPAPP": "mdi:newspaper",
    "SLAM": "mdi:water-pump",
    "TRÄDGÅRD": "mdi:leaf",
    "WELLPAPP": "mdi:package-variant",
}
DEFAULT_ICON = "mdi:trash-can"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your address at https://www.telge.se by searching for your street name in the waste collection schedule (Sopbilsschema). Use the exact address string shown in the autocomplete dropdown, e.g. 'BERGSGATAN 22, SÖDERTÄLJE'.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Exact address as shown in the Telge autocomplete (uppercase, e.g. BERGSGATAN 22, SÖDERTÄLJE)",
    },
}


class Source:
    def __init__(self, address: str):
        if not address:
            raise SourceArgumentRequired(
                "address",
                "An address is required (use the autocomplete endpoint to find "
                "the exact format, e.g. 'BERGSGATAN 22, SÖDERTÄLJE')",
            )
        self._address = address.strip().upper()

    def fetch(self) -> list[Collection]:
        r = requests.get(
            f"{API_URL}/schedule/{self._address}",
            timeout=30,
        )
        r.raise_for_status()

        data = r.json()

        if not isinstance(data, list) or not data:
            suggestions = self._autocomplete(self._address.split(",")[0].strip())
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "address", self._address, suggestions
                )
            raise SourceArgumentNotFound("address", self._address)

        entries = []
        for item in data:
            waste_type = item.get("typeOfWaste", "").strip()
            waste_description = item.get("typeOfWasteDescription", waste_type).strip()
            container_type = item.get("containerType", "").strip()
            dt = datetime.fromisoformat(item["date"])

            # Distinguish bins: K370L1 → "(kärl 1)", K140L → no suffix
            m = re.search(r"L(\d+)$", container_type)
            if m:
                waste_description += f" (kärl {m.group(1)})"

            entries.append(
                Collection(
                    date=dt.date(),
                    t=waste_description,
                    icon=ICON_MAP.get(waste_type, DEFAULT_ICON),
                )
            )

        return entries

    @staticmethod
    def _autocomplete(query: str) -> list[str]:
        try:
            r = requests.get(
                f"{API_URL}/autocomplete/{query}",
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return []
