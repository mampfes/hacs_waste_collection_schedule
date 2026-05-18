import re
from typing import List

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Eilenburg"
DESCRIPTION = "Source for waste collection in Eilenburg (Saxony, Germany)."
URL = "https://www.eilenburg.de"
COUNTRY = "de"
TEST_CASES = {
    "EB Berg + EB 1": {"areas": ["EB Berg", "EB 1"]},
    "EB Stadt + EB 3": {"areas": ["EB Stadt", "EB 3"]},
    "EB Ortsteile": {"areas": ["EB Ortsteile Dörfer"]},
}

PARAM_TRANSLATIONS = {
    "de": {
        "areas": "Entsorgungsbezirke",
    },
    "en": {
        "areas": "Collection areas",
    },
}

PARAM_DESCRIPTIONS = {
    "de": {
        "areas": "Liste der Entsorgungsbezirke, z. B. ['EB Berg', 'EB 1']. Restmüll/Papier-Bezirke: EB Berg, EB Stadt, EB Ost, EB Ortsteile Dörfer. Gelber-Sack-Bezirke: EB 1 bis EB 5.",
    },
    "en": {
        "areas": "List of collection areas, e.g. ['EB Berg', 'EB 1']. Residual/paper areas: EB Berg, EB Stadt, EB Ost, EB Ortsteile Dörfer. Yellow-bag areas: EB 1 to EB 5.",
    },
}

CALENDAR_PAGE_URL = (
    "https://www.eilenburg.de/portal/seiten/abfallwirtschaft-900000136-27670.html"
)

ICS_LINK_PATTERN = re.compile(
    r'data-extension="ICS"[^>]*href="(https://www\.eilenburg\.de/downloads/datei/[^"]+)"[^>]*title="[^"]*&quot;([^&]+\.ics)&quot;'
)
AREA_NAME_PATTERN = re.compile(r"- (EB .+?)\.ics$")


class Source:
    def __init__(self, areas: List[str]):
        self._areas = areas
        self._ics = ICS()

    def fetch(self) -> List[Collection]:
        # Fetch the waste calendar page
        r = requests.get(
            CALENDAR_PAGE_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()
        html = r.text

        # Extract all ICS download links and their area names
        available: dict[str, str] = {}
        for ics_url, filename in ICS_LINK_PATTERN.findall(html):
            m = AREA_NAME_PATTERN.search(filename)
            if m:
                area_name = m.group(1)
                available[area_name] = ics_url

        entries: List[Collection] = []
        for area in self._areas:
            # Case-insensitive match
            matched_url = None
            for available_area, ics_url in available.items():
                if available_area.lower() == area.lower():
                    matched_url = ics_url
                    break

            if matched_url is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "areas",
                    area,
                    list(available.keys()),
                )

            ics_r = requests.get(
                matched_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            ics_r.raise_for_status()
            ics_text = ics_r.text

            for date, waste_type in self._ics.convert(ics_text):
                entries.append(Collection(date, waste_type))

        return entries
