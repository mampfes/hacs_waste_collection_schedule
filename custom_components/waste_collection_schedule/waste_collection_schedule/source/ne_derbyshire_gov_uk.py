"""North East Derbyshire District Council (UK).

Two public sources are combined:

1. The council's AchieveForms "Self" portal still answers the lookup behind its
   (now unlisted) "Check your Bin Day" form: runLookup ``60140920c3f20`` takes
   the property's UPRN and returns its ``Route``, a weekday abbreviation plus
   the calendar area, e.g. ``FrN`` (Friday, North) or ``MoS`` (Monday, South).
2. The "Bin Collection Dates" page publishes, per area, which bins are emptied
   in which *week* ("Monday 3rd to Friday 7th August: Black Bin and Food Caddy
   collections."), including the weeks shifted by a bank holiday ("Tuesday 1st
   to Saturday 5th September ... one day later") and the Christmas changes.

The household's date is its route weekday inside the published week, moved one
day later in a shifted (Tuesday-Saturday) week. A one-day replacement entry
("Tuesday 29th December ... if your bin should have been emptied on the 25th")
applies only to the round whose usual day is the one named.
"""

import datetime
import re
from typing import Any, ClassVar, final

from bs4 import Tag
from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.recurrence import month as month_number
from waste_collection_schedule.recurrence import weekday as weekday_number
from waste_collection_schedule.retrievers import FanOutRetriever
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
    lookup_context,
)
from waste_collection_schedule.transformers import RowTransformer

HOSTNAME = "myselfservice.ne-derbyshire.gov.uk"
LOOKUP_ID = "60140920c3f20"
DATES_URL = "https://www.ne-derbyshire.gov.uk/bins-and-recycling/bin-collection-dates"

_AREAS = {"N": "north", "S": "south"}
_ROUTE_DAYS = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4}

_DAY = (
    r"(?P<{p}wd>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
    r"(?P<{p}d>\d{{1,2}})(?:st|nd|rd|th)?"
    r"(?:\s+(?P<{p}m>January|February|March|April|May|June|July|August|"
    r"September|October|November|December))?"
    r"(?:\s+(?P<{p}y>\d{{4}}))?"
)
_ENTRY_RE = re.compile(
    rf"^{_DAY.format(p='s')}(?:\s+to\s+{_DAY.format(p='e')})?\s*:\s*(?P<what>.*)$",
    re.IGNORECASE,
)
# "August 2026", "December '26", "January 27"
_HEADING_RE = re.compile(r"^[A-Za-z]+\s+'?(?P<y>\d{2}|\d{4})$")
_REPLACES_RE = re.compile(r"emptied on the (\d{1,2})(?:st|nd|rd|th)?", re.IGNORECASE)
_BINS = {
    "Black Bin": re.compile(r"\bb\s*lack\b", re.IGNORECASE),
    "Burgundy Bin": re.compile(r"\bburgundy\b", re.IGNORECASE),
    "Green Bin": re.compile(r"\bgreen\b", re.IGNORECASE),
    "Food Caddy": re.compile(r"\bfood caddy\b", re.IGNORECASE),
}


def _store_route(response: dict, context: dict[str, Any]) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data")
    rows = list(rows.values()) if isinstance(rows, dict) else list(rows or [])
    if rows:
        context["route"] = str(rows[0].get("Route") or "").strip()


def _dates_page(source: BaseSource, _response: Any) -> list[str]:
    """The dates page, once the UPRN has resolved to a known route."""
    route = lookup_context(source).get("route", "")
    if route[:2].lower() not in _ROUTE_DAYS or route[-1:].upper() not in _AREAS:
        raise SourceArgumentNotFound(
            "uprn",
            source.params["uprn"],
            "the council has no bin round for this UPRN; check it on "
            "https://www.findmyaddress.co.uk/",
        )
    return [DATES_URL]


def _date(match: re.Match, p: str, month: int | None, year: int) -> datetime.date:
    m = month_number(match.group(f"{p}m")) if match.group(f"{p}m") else month
    y = int(match.group(f"{p}y")) if match.group(f"{p}y") else year
    return datetime.date(y, m, int(match.group(f"{p}d")))  # type: ignore[arg-type]


def _parse_range(
    match: re.Match, year: int
) -> tuple[datetime.date, datetime.date] | None:
    if match.group("ewd"):
        end = _date(match, "e", None, year) if match.group("em") else None
        if end is None:
            return None
        if match.group("sm"):
            start_month = month_number(match.group("sm"))
        else:
            start_month = end.month
            if int(match.group("sd")) > end.day:
                start_month = end.month - 1 or 12
        start_year = end.year - 1 if (start_month or 0) > end.month else end.year
        start = _date(match, "s", start_month, start_year)
    else:
        if not match.group("sm"):
            return None
        start = end = _date(match, "s", None, year)
    for p, day in (("s", start), ("e", end)):
        name = match.group(f"{p}wd")
        if name and weekday_number(name) != day.weekday():
            return None
    return start, end


def _rows(panels: list[Tag], source: BaseSource) -> list[tuple[datetime.date, str]]:
    """``(date, bin)`` rows for this household's area and route weekday."""
    route = lookup_context(source)["route"]
    area = _AREAS[route[-1].upper()]
    route_day = _ROUTE_DAYS[route[:2].lower()]

    rows: set[tuple[datetime.date, str]] = set()
    for panel in panels:
        if area not in str(panel.get("id", "")).lower():
            continue
        year = datetime.date.today().year
        for element in panel.find_all(["h4", "p", "li"]):
            if element.name == "p" and element.find_parent("li"):
                continue
            text = " ".join(element.get_text(" ", strip=True).split())
            heading = _HEADING_RE.match(text)
            if heading and month_number(text.split()[0]):
                y = int(heading.group("y"))
                year = y if y > 100 else 2000 + y
                continue
            match = _ENTRY_RE.match(text)
            if not match:
                continue
            what = match.group("what")
            bins = [label for label, pattern in _BINS.items() if pattern.search(what)]
            if not bins or re.search(r"\bno collections\b", what, re.IGNORECASE):
                continue
            span = _parse_range(match, year)
            if span is None:
                continue
            start, end = span
            year = end.year

            replaces = _REPLACES_RE.search(what)
            if replaces:
                # A one-off day standing in for the usual day named here.
                usual_day = int(replaces.group(1))
                usual = start.replace(day=usual_day)
                if usual > start:
                    usual = (start.replace(day=1) - datetime.timedelta(days=1)).replace(
                        day=usual_day
                    )
                if usual.weekday() == route_day:
                    rows.update((start, label) for label in bins)
                continue

            # A bank holiday moves the whole week one day later (Tue-Sat).
            shift = 1 if start.weekday() == 1 and end.weekday() == 5 else 0
            monday = start - datetime.timedelta(days=start.weekday())
            while monday <= end:
                day = monday + datetime.timedelta(days=route_day + shift)
                if start <= day <= end:
                    rows.update((day, label) for label in bins)
                monday += datetime.timedelta(weeks=1)
    return sorted(rows)


@final
class Source(BaseSource):
    TITLE = "North East Derbyshire District Council"
    DESCRIPTION = "Source for North East Derbyshire District Council, UK."
    URL = "https://www.ne-derbyshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Dronfield Woodhouse (North, Friday)": {"uprn": "100030223463"},
        "Wingerworth (South, Monday)": {"uprn": 100030201500},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown UPRN": {"uprn": "100030260000"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find the UPRN of your property at https://www.findmyaddress.co.uk/. "
            "Your collection weekday and North/South calendar are looked up from "
            "it; the dates come from the council's bin collection dates page."
        ),
    }

    retrieve = FanOutRetriever(
        prepare=AchieveFormsRetriever(
            hostname=HOSTNAME,
            initial_url=f"https://{HOSTNAME}/",
            steps=[
                LookupStep(
                    LOOKUP_ID,
                    form_values=lambda ctx, source: {
                        "uprnLoggedIn": {"value": str(source.params["uprn"])}
                    },
                    no_retry="true",
                    extract=_store_route,
                ),
            ],
        ),
        targets=_dates_page,
    )
    parse = parsers.EachResponse(
        parsers.HtmlParser(
            'div[data-rlta-element="panel"]',
            require=['div[data-rlta-element="panel"]'],
        )
    )
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        type_value_map={
            "Black Bin": wt.GENERAL_WASTE,
            "Burgundy Bin": wt.RECYCLABLES,
            "Green Bin": wt.GARDEN_WASTE,
            "Food Caddy": wt.FOOD_WASTE,
        },
    )
