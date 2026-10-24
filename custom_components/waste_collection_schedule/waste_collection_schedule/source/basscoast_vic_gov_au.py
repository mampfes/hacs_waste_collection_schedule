"""Bass Coast Shire Council, Victoria, Australia.

The council publishes one bin calendar per collection zone and season
(September to August) on
https://www.basscoast.vic.gov.au/services/waste-rubbish/kerbside-bin-collection.
Its month grids paint every collection day of a week in the colour of what is
collected that week: red for landfill and organics, yellow for recycling and
organics, dark green for landfill, recycling and organics. The household's bins
go out on its zone's collection day for its suburb.
"""

import datetime
import re
from collections.abc import Iterable
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://www.basscoast.vic.gov.au"
_INDEX_URL = f"{_URL}/services/waste-rubbish/kerbside-bin-collection"

LANDFILL = "Landfill"
RECYCLING = "Recycling"
ORGANICS = "Organics"

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_ZONE = re.compile(r"^Zone\s*(\d)\b", re.IGNORECASE)

_CELL_WIDTH = (13.0, 19.0)
_CELL_HEIGHT = (11.0, 15.0)


def _zone(link: Tag) -> str:
    """'Zone 1 - Bin Calendar September 2026-2027' -> '1'."""
    match = _ZONE.match(link.get_text(" ", strip=True))
    return match.group(1) if match else ""


def _collection_days(
    rows: list[tuple[datetime.date, str]], source: BaseSource | None = None
) -> Iterable[tuple[datetime.date, str]]:
    """Keep the household's collection day of every painted week."""
    weekday = _DAYS.index(source.params["collection_day"]) if source else None
    for day, label in rows:
        if weekday is None or day.weekday() == weekday:
            yield day, label


@final
class Source(BaseSource):
    TITLE = "Bass Coast Shire Council"
    DESCRIPTION = (
        "Source for Bass Coast Shire Council (Victoria) kerbside bin calendars."
    )
    URL = _URL
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Zone 1, Wednesday (Grantville)": {"zone": "1", "collection_day": "Wednesday"},
        "Zone 2, Monday": {"zone": "2", "collection_day": "Monday"},
    }

    PARAMS = (
        config_params.dropdown("zone", ["1", "2"], label="Zone"),
        config_params.dropdown("collection_day", _DAYS, label="Collection day"),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open the bin calendar of your zone on "
            "https://www.basscoast.vic.gov.au/services/waste-rubbish/kerbside-bin-collection; "
            "the foot of the calendar lists the collection day of every suburb "
            "of the zone. Choose the zone and that day."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL, pick=lookups.link_pick("zone", label=_zone, newest=True)
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(
                f"{LANDFILL}, {ORGANICS}",
                (0.05, 1.0, 0.89, 0.22),
                width=_CELL_WIDTH,
                height=_CELL_HEIGHT,
            ),
            Marker(
                f"{RECYCLING}, {ORGANICS}",
                (0.0, 0.22, 1.0, 0.0),
                width=_CELL_WIDTH,
                height=_CELL_HEIGHT,
            ),
            Marker(
                f"{LANDFILL}, {RECYCLING}, {ORGANICS}",
                (1.0, 0.57, 0.12, 0.61),
                width=_CELL_WIDTH,
                height=_CELL_HEIGHT,
            ),
        ],
        placement="cell",
        weekdays="MTWTFSS",
        first_month=None,
        year_pattern=(
            r"(?:January|February|March|April|May|June|July|August|September"
            r"|October|November|December)\s+(20\d{2})"
        ),
    )
    preprocess = preprocessors.Compose(
        preprocessors.SplitLabels(","),
        _collection_days,
    )
    transform = ICSTransformer(
        type_value_map={
            LANDFILL: wt.GENERAL_WASTE,
            RECYCLING: wt.RECYCLABLES,
            ORGANICS: wt.ORGANIC,
        }
    )
