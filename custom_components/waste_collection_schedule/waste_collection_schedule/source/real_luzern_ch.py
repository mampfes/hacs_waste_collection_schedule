"""Real Luzern (real-luzern.ch), Switzerland.

Demonstrates: a two-step flow where the lookup page (keyed by municipality +
optional street id) is scraped for a tour id and its enabled waste-type
categories, which are then folded into the final ICS-download request via
``TwoStepRetriever``. The category set varies per municipality, so the
"key" the extractor returns is the whole download-params dict rather than a
bare id.
"""

from typing import ClassVar, final
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import ICSTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.real-luzern.ch/abfall/sammeldienst/abfallkalender/"

# New fetcher uses different (longer) names; remapped to the original short
# names before mapping, so existing customisations / TEST_CASES keep working.
_OLD_WASTE_NAME = {
    "Kehrichtsammlung": "Kehricht",
    "Grüngutsammlung": "Grüngut",
    "Papiersammlung": "Papier",
    "Kartonsammlung": "Karton",
    "Alteisen/Metallsammlung": "Altmetall",
}


def _extract_ics_params(lookup, source) -> dict:
    soup = BeautifulSoup(lookup.text, features="html.parser")
    data_div = soup.select_one("div.abfk-calendar.abfk-colors")
    if not data_div:
        raise ValueError("No data found")

    tour_id = data_div.get("data-tourid")
    if not tour_id:
        raise ValueError("No tour id found")
    categories = data_div.get("data-categories")
    if not categories:
        raise ValueError("No categories found")

    return {
        "abfk_calendar_download": "1",
        "calendar[tourId]": str(tour_id),
        "calendar[gemeinde]": "Luzern",
        "calendar[format]": "ics",
        **{
            f"calendar[{category}]": category for category in str(categories).split(",")
        },
    }


def _schedule_url(ics_params: dict, **_) -> str:
    return f"{_API_URL}?{urlencode(ics_params)}"


@final
class Source(BaseSource):
    TITLE = "Real Luzern"
    DESCRIPTION = "Source script for Real Luzern, Switzerland"
    URL = "https://www.real-luzern.ch"
    COUNTRY = "ch"

    TEST_CASES: ClassVar[dict] = {
        "Luzern - Heimatweg": {"municipality_id": 13, "street_id": 766},
        "Luzern - Pliatusblick": {"municipality_id": 13, "street_id": 936},
        "Emmen": {"municipality_id": 6},
    }

    PARAMS = (
        text_field("municipality_id", label="Municipality ID"),
        text_field("street_id", label="Street ID", optional=True),
    )

    RAISE_ON_EMPTY = True

    retrieve = TwoStepRetriever(
        lookup_url=lambda municipality_id, street_id=None, **_: (
            f"{_API_URL}?gemid={municipality_id}&strid={street_id}"
        ),
        extract=_extract_ics_params,
        schedule_url=_schedule_url,
    )
    parse = parsers.IcsParser()

    transform = ICSTransformer(
        type_value_map={
            "Kehricht": GENERAL_WASTE,
            "Grüngut": ORGANIC,
            "Papier": PAPER,
            "Karton": PAPER,
            "Altmetall": RECYCLABLES,
        },
        clean=label_cleaner(remap=_OLD_WASTE_NAME),
    )

    def __init__(
        self, municipality_id: "str | int", street_id: "str | int | None" = None
    ):
        super().__init__(municipality_id=municipality_id, street_id=street_id)
