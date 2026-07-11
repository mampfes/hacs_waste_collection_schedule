"""Pointe-Claire (QC) (pointe-claire.ca).

Demonstrates: a static ICS GET whose URL is a fixed per-sector lookup (an
invalid sector raises ``SourceArgumentNotFoundWithSuggestions``, same as the
legacy source) rather than a URL template. ``HttpGetRetriever`` + the
extended ``IcsParser`` + ``ICSTransformer`` do the rest.

The legacy source's suffix-strip regex targeted "(Sector A)" (with
parentheses), but the feed's actual suffix is " - Sector A" (a dash) — the
strip never matched, so every summary (and every ``ICON_MAP`` lookup against
it) carried the redundant sector suffix and always missed, showing no icon
for any collection. Fixed here: the ``IcsParser`` regex matches the real
suffix, and every observed category (including three the old ``ICON_MAP``
never covered at all: Ecocentre, Leaf and Mattress/Box-Spring collections)
is mapped to a canonical type.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

_SECTOR_URL_MAP: dict[str, str] = {
    "A": "https://raw.githubusercontent.com/jordanconway/pointe-claire-waste-calendars/refs/heads/main/pointe-claire-a.ics",
    "B": "https://raw.githubusercontent.com/jordanconway/pointe-claire-waste-calendars/refs/heads/main/pointe-claire-b.ics",
}


def _sector_url(sector: str, **_) -> str:
    key = str(sector).upper().strip()
    url = _SECTOR_URL_MAP.get(key)
    if url is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "sector", sector, list(_SECTOR_URL_MAP.keys())
        )
    return url


@final
class Source(BaseSource):
    TITLE = "Pointe-Claire (QC)"
    DESCRIPTION = "Source for Pointe-Claire, Québec waste collection schedules."
    URL = "https://www.pointe-claire.ca"
    COUNTRY = "ca"

    TEST_CASES: ClassVar[dict] = {
        "Sector A": {"sector": "A"},
        "Sector B": {"sector": "B"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Find your collection sector on the City of Pointe-Claire website at"
            " https://www.pointe-claire.ca/en/residents/public-works/"
            "waste-management/"
        ),
        "fr": (
            "Trouvez votre secteur de collecte sur le site de la Ville de"
            " Pointe-Claire à https://www.pointe-claire.ca/residents/"
            "travaux-publics/gestion-des-dechets/"
        ),
    }

    PARAMS = (dropdown("sector", ["A", "B"], label="Sector"),)

    retrieve = HttpGetRetriever(url=_sector_url)
    parse = parsers.IcsParser(regex=r"^(.*?)\s*-\s*Sector [AB]$")
    transform = ICSTransformer(
        type_value_map={
            "Household Waste": GENERAL_WASTE,
            "Recyclables": RECYCLABLES,
            "Organic Waste": ORGANIC,
            "Bulky Items": BULKY_WASTE,
            "Mattress/Box-Spring Collection": BULKY_WASTE,
            "Christmas Tree Collection": GARDEN_WASTE,
            "Leaf Collection": GARDEN_WASTE,
        }
    )

    def __init__(self, sector: str):
        super().__init__(sector=sector)
