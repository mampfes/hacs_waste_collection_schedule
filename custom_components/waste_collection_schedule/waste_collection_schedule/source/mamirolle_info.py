import datetime
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.transformers import HtmlTransformer

_BINS = {"poubelle-grise": "Poubelle grise", "poubelle-jaune": "Poubelle jaune"}


def _bin(heading: Tag) -> str:
    """The bin named by the icon preceding a date heading."""
    icon = heading.find_previous_sibling("i")
    classes = (icon.get("class") or []) if isinstance(icon, Tag) else []
    return next(_BINS[c] for c in classes if c in _BINS)


def _date(heading: Tag) -> datetime.date:
    """``Jeudi 1er octobre`` as its next occurrence (the page shows no year)."""
    _, day, month_name = heading.get_text(strip=True).split()
    month = recurrence.month(month_name)
    if month is None:
        raise ValueError(f"unknown month {month_name!r}")
    today = datetime.date.today()
    number = int("".join(c for c in day if c.isdigit()))
    found = datetime.date(today.year, month, number)
    if found < today:
        found = found.replace(year=today.year + 1)
    return found


@final
class Source(BaseSource):
    TITLE = "Mairie de Mamirolle"
    DESCRIPTION = "Source script for mamirolle.info"
    URL = "http://mamirolle.info/"
    COUNTRY = "fr"

    TEST_CASES: ClassVar[dict] = {"TestSource": {}}

    PARAMS = ()
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    retrieve = retrievers.HttpGetRetriever(url="http://mamirolle.info/")
    parse = parsers.HtmlParser("#poubelles h4", require=["#poubelles"])
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_bin,
        type_value_map={
            "Poubelle grise": wt.GENERAL_WASTE,
            "Poubelle jaune": wt.RECYCLABLES,
        },
    )
