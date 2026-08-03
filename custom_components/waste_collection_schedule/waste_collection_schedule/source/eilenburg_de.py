"""Eilenburg (Saxony, Germany).

Demonstrates ``IcsIndexRetriever``'s labelled selection: there is one ICS feed
per collection area, and the feeds are only discoverable by scraping the
municipality's calendar page. Each download link is named by the ``.ics``
filename quoted in its title attribute, and the ``areas`` argument picks which
of those the user belongs to.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsIndexRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The feed labels each pickup "<service> - EB <zone>", e.g.
# "Restabfallentsorgung - EB Berg" or "Entsorgung gelber Sack - EB 1", which the
# shared vocabulary does not match. Reduce the label to its core waste term for
# the type_value_map.
_TYPE_VALUE_MAP = {
    "restabfall": wt.GENERAL_WASTE,
    "gelber sack": wt.RECYCLABLES,
    "papier": wt.PAPER,
}


def _clean(label: str) -> str:
    text = label.lower()
    if "restabfall" in text or "restmüll" in text:
        return "restabfall"
    if "gelber sack" in text or "gelbe" in text or "wertstoff" in text:
        return "gelber sack"
    if "papier" in text:
        return "papier"
    return label


_CALENDAR_PAGE_URL = (
    "https://www.eilenburg.de/portal/seiten/abfallwirtschaft-900000136-27670.html"
)

# Each download link's title attribute quotes the file it serves, e.g.
# '© Stadt Eilenburg. "Abfallkalender Remondis 2026 - EB Berg.ics" .'
_ICS_FILENAME_PATTERN = re.compile(r'"([^"]+\.ics)"')
_AREA_NAME_PATTERN = re.compile(r"- (EB .+?)\.ics$")


def _area_name(anchor) -> str | None:
    """The collection area a download link serves, read off its title."""
    filename = _ICS_FILENAME_PATTERN.search(str(anchor.get("title") or ""))
    if filename is None:
        return None
    area = _AREA_NAME_PATTERN.search(filename.group(1))
    return area.group(1) if area else None


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

    retrieve = IcsIndexRetriever(
        index_url=_CALENDAR_PAGE_URL,
        link_selector='a[data-extension="ICS"]',
        pattern=r"/downloads/datei/",
        label=_area_name,
        argument="areas",
        headers={"User-Agent": "Mozilla/5.0"},
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(clean=_clean, type_value_map=_TYPE_VALUE_MAP)

    def __init__(self, areas: list[str] | str):
        if isinstance(areas, str):
            areas = [a.strip() for a in areas.split(",") if a.strip()]
        super().__init__(areas=areas)
