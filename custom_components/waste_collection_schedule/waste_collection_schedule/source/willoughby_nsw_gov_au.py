from __future__ import annotations

import re

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesClient,
    OpenCitiesConfig,
)

TITLE = "Willoughby City Council"
DESCRIPTION = "Source for Willoughby City Council waste collection."
URL = "https://www.willoughby.nsw.gov.au"
COUNTRY = "au"

TEST_CASES = {
    "18 Crabbes Avenue, North Willoughby": {
        "address": "18 Crabbes Avenue, North Willoughby, NSW 2068",
    },
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Green Waste": Icons.GARDEN,
    "Bulky Waste": Icons.BULKY,
    "Street Sweeping": Icons.GENERAL_WASTE,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address, for example: 18 Crabbes Avenue, North Willoughby, NSW 2068",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit the Willoughby City Council waste service dates page, search for your address, and use the address text as shown by the lookup.",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": (
        f"{URL}/Residents/Waste-and-recycling/"
        "Household-bin-services/Waste-and-street-sweeping-services"
    ),
    "X-Requested-With": "XMLHttpRequest",
}

_CONFIG = OpenCitiesConfig(
    domain=URL,
    headers=HEADERS,
    icon_keywords=ICON_MAP,
    use_curl_cffi=True,
)


def _normalise_waste_type(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    lower = text.lower()

    if "recycl" in lower:
        return "Recycling"
    if "green" in lower or "garden" in lower or "organics" in lower or "fogo" in lower:
        return "Green Waste"
    if "bulky" in lower or "clean" in lower:
        return "Bulky Waste"
    if "sweep" in lower:
        return "Street Sweeping"
    if "general" in lower or "rubbish" in lower or "garbage" in lower:
        return "General Waste"

    return text


class Source:
    def __init__(self, address: str):
        self._address = address.strip()
        self._client = OpenCitiesClient(_CONFIG)

    def fetch(self) -> list[Collection]:
        raw_entries = self._client.fetch(address=self._address)

        entries: list[Collection] = []
        seen: set[tuple[object, str]] = set()
        for entry in raw_entries:
            waste_type = _normalise_waste_type(entry.type)
            key = (entry.date, waste_type)
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                Collection(
                    date=entry.date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )
        return entries
