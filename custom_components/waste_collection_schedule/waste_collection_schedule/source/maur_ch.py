"""Source for Gemeinde Maur, Switzerland."""

import datetime
import re
from typing import ClassVar, final

from bs4 import Tag
from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import EachResponse, HtmlParser
from waste_collection_schedule.preprocessors import Deduplicate
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import HtmlTransformer

_TERMINE_URL = (
    "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html/924"
)

# The event list is paginated: page 1 is the bare URL, the others carry this
# suffix, and page 1 links to each of them.
_PAGE_SUFFIX = "/eventsjsRequest/0/eventspage/{page}"
_PAGE_LINK = re.compile(r"eventspage/(\d+)")
_DATE = re.compile(r"(\d{1,2})\.\s*([A-Za-zäöüß]+)\s+(\d{4})")


_PAGE = Request(lambda page_url, _first, **_: page_url)


def _page_urls(source: BaseSource, first) -> list:
    """The first response, then the URL of every further page it links to."""
    last = max((int(page) for page in _PAGE_LINK.findall(first.text)), default=1)
    return [
        first,
        *(_TERMINE_URL + _PAGE_SUFFIX.format(page=page) for page in range(2, last + 1)),
    ]


def _label(tag: Tag) -> str:
    link = tag.select_one("h2.mod-entry-title a")
    return link.get_text(strip=True) if link else ""


def _date(tag: Tag) -> datetime.date | None:
    # The datetime attribute holds the start of the recurring series, not the
    # occurrence, so the visible text is read instead.
    time_tag = tag.select_one("time.dtstart")
    match = _DATE.match(time_tag.get_text(strip=True)) if time_tag else None
    month = recurrence.month(match.group(2)) if match else None
    if match is None or month is None:
        return None
    return datetime.date(int(match.group(3)), month, int(match.group(1)))


def _normalise(label: str) -> str:
    """One label per service: the provider appends dates and districts to them."""
    lowered = label.lower()
    if "häcksel" in lowered:
        return "Häcksel-Service"
    if "hauptsammelstelle" in lowered:
        return "Hauptsammelstelle"
    return label.strip()


@final
class Source(BaseSource):
    TITLE = "Gemeinde Maur"
    DESCRIPTION = "Source for waste collection in Maur, Canton of Zurich, Switzerland."
    URL = "https://www.maur.ch/themen/bauen-umwelt/abfall-recycling/termine.html"
    COUNTRY = "ch"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {"Maur": {}}

    PARAMS = ()

    HOWTO: ClassVar[dict] = {
        "en": (
            "Maur publishes a single municipality-wide collection calendar, "
            "so no address or other argument is required."
        ),
        "de": (
            "Maur veröffentlicht einen einzigen gemeindeweiten Abfallkalender, "
            "daher ist kein Argument erforderlich."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = FanOutRetriever(
        prepare=Lookup(_TERMINE_URL, pick=lambda response, **_: response),
        targets=_page_urls,
        fetch=lambda source, target, first: (
            first if target is first else _PAGE(source, target, first)
        ),
    )
    parse = EachResponse(
        HtmlParser("li.mod-entry.event-item", require=["li.mod-entry.event-item"])
    )
    preprocess = Deduplicate(key=lambda tag: (_date(tag), _normalise(_label(tag))))
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=lambda tag: _normalise(_label(tag)),
        type_value_map={
            "Kehricht": wt.GENERAL_WASTE,
            "Grüngut": wt.GARDEN_WASTE,
            "Grüngut/Christbaum": wt.GARDEN_WASTE,
            "Häcksel-Service": wt.GARDEN_WASTE,
            "Karton": wt.PAPER,
            "Papiersammlung": wt.PAPER,
            "Sonderabfall": wt.HAZARDOUS,
            "Metall": wt.RECYCLABLES,
            "Hauptsammelstelle": wt.RECYCLABLES,
        },
    )
