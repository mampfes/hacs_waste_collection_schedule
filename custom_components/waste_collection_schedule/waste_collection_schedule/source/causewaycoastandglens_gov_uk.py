"""Causeway Coast and Glens Borough Council, Northern Ireland.

The council publishes one yearly black and blue bin calendar per former council
area (Ballymoney, Coleraine, Limavady, Moyle) on
https://causewaycoastandglens.gov.uk/live/bins-and-recycling/bin-collections/collection-calendars.
Its twelve month grids paint every working day of a week blue (blue bin week)
or grey (black bin week); the bin is emptied on the household's normal
collection day within that week.
"""

import datetime
from collections.abc import Iterable
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import config_params, lookups, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.service.PdfMarkerCalendar import (
    Marker,
    MarkerCalendarParser,
)
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://causewaycoastandglens.gov.uk"
_INDEX_URL = f"{_URL}/live/bins-and-recycling/bin-collections/collection-calendars"

BLUE = "Blue bin"
BLACK = "Black bin"

_AREAS = ["Ballymoney", "Coleraine", "Limavady", "Moyle"]
_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

_CELL_WIDTH = (20.0, 30.0)
_CELL_HEIGHT = (15.0, 25.0)


def _area(link: Tag) -> str:
    """'Coleraine area Black and Blue Bin Calendar 2026 ...' -> 'Coleraine'."""
    text = link.get_text(" ", strip=True)
    return text.split(" area ", 1)[0] if " area " in text else ""


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
    TITLE = "Causeway Coast and Glens Borough Council"
    DESCRIPTION = "Source for Causeway Coast and Glens Borough Council black and blue bin calendars."
    URL = _URL
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Coleraine, Tuesday": {"area": "Coleraine", "collection_day": "Tuesday"},
        "Moyle, Friday": {"area": "Moyle", "collection_day": "Friday"},
    }

    PARAMS = (
        config_params.dropdown("area", _AREAS, label="Area"),
        config_params.dropdown("collection_day", _DAYS, label="Collection day"),
    )

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Choose your former council area (Ballymoney, Coleraine, Limavady or "
            "Moyle) as on "
            "https://causewaycoastandglens.gov.uk/live/bins-and-recycling/bin-collections/collection-calendars, "
            "and your normal bin collection day. Collection changes for bank "
            "holidays are announced by the council separately and are not part "
            "of the calendar."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _INDEX_URL,
                pick=lookups.link_pick(
                    "area", href=r"/assets/files/.*\.pdf$", label=_area
                ),
            ),
        ),
        url=lambda pdf_url, **_: pdf_url,
        timeout=60,
    )
    parse = MarkerCalendarParser(
        [
            Marker(
                BLUE, (0.77, 0.22, 0.0, 0.0), width=_CELL_WIDTH, height=_CELL_HEIGHT
            ),
            Marker(
                BLACK,
                (0.47, 0.37, 0.36, 0.16),
                width=_CELL_WIDTH,
                height=_CELL_HEIGHT,
            ),
        ],
        placement="cell",
        weekdays="MTWTF",
        pages=(0,),
        year_pattern=r"Calendar\s+(20\d{2})",
    )
    preprocess = staticmethod(_collection_days)
    transform = ICSTransformer(
        type_value_map={BLUE: wt.RECYCLABLES, BLACK: wt.GENERAL_WASTE}
    )
