"""Eilenburg (Saxony, Germany).

Demonstrates: the "discover feeds from an HTML index, fan out across
selected named areas" shape. There is one ICS feed per collection area; the
list of feeds (and their download URLs) is only discoverable by scraping the
municipality's calendar page, so ``retrieve`` scrapes that page once, then
fetches one feed per area the user asked for.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS
from waste_collection_schedule.transformers import ICSTransformer

_CALENDAR_PAGE_URL = (
    "https://www.eilenburg.de/portal/seiten/abfallwirtschaft-900000136-27670.html"
)

_ICS_LINK_PATTERN = re.compile(
    r'data-extension="ICS"[^>]*href="(https://www\.eilenburg\.de/downloads/datei/[^"]+)"[^>]*title="[^"]*&quot;([^&]+\.ics)&quot;'
)
_AREA_NAME_PATTERN = re.compile(r"- (EB .+?)\.ics$")


@final
class Source(BaseSource):
    TITLE = "Eilenburg"
    DESCRIPTION = "Source for waste collection in Eilenburg (Saxony, Germany)."
    URL = "https://www.eilenburg.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "EB Berg + EB 1": {"areas": ["EB Berg", "EB 1"]},
        "EB Stadt + EB 3": {"areas": ["EB Stadt", "EB 3"]},
        "EB Ortsteile": {"areas": ["EB Ortsteile Dörfer"]},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "List of collection areas, e.g. ['EB Berg', 'EB 1']. Residual/paper "
            "areas: EB Berg, EB Stadt, EB Ost, EB Ortsteile Dörfer. Yellow-bag "
            "areas: EB 1 to EB 5."
        ),
        "de": (
            "Liste der Entsorgungsbezirke, z. B. ['EB Berg', 'EB 1']. "
            "Restmüll/Papier-Bezirke: EB Berg, EB Stadt, EB Ost, EB Ortsteile "
            "Dörfer. Gelber-Sack-Bezirke: EB 1 bis EB 5."
        ),
    }

    PARAMS = (text_field("areas", "Collection areas"),)

    def retrieve(self, source):
        r = self.session.get(
            _CALENDAR_PAGE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
        )
        r.raise_for_status()
        html = r.text

        available: dict[str, str] = {}
        for ics_url, filename in _ICS_LINK_PATTERN.findall(html):
            m = _AREA_NAME_PATTERN.search(filename)
            if m:
                available[m.group(1)] = ics_url

        texts: list[str] = []
        for area in self.params["areas"]:
            matched_url = None
            for available_area, ics_url in available.items():
                if available_area.lower() == area.lower():
                    matched_url = ics_url
                    break

            if matched_url is None:
                raise SourceArgumentNotFoundWithSuggestions(
                    "areas", area, list(available.keys())
                )

            ics_r = self.session.get(
                matched_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
            )
            ics_r.raise_for_status()
            texts.append(ics_r.text)

        return texts

    def parse(self, response, source=None):
        entries: list = []
        for text in response:
            entries.extend(ICS().convert(text))
        return entries

    transform = ICSTransformer()

    def __init__(self, areas: list[str] | str):
        if isinstance(areas, str):
            areas = [a.strip() for a in areas.split(",") if a.strip()]
        super().__init__(areas=areas)
