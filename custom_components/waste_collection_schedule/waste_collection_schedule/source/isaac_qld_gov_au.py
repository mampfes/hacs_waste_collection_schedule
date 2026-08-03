import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
)
from waste_collection_schedule.exceptions import SourceArgumentRequired
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

# Demonstrates: scraping a town-wide collection weekday out of static HTML,
# resolving the chosen town with ArgumentLookup, then projecting the result into
# a weekly schedule with RecurrenceExpander + ICSTransformer; plus a manual
# day-select fallback for providers with no address lookup.
#
# Isaac Regional Council (issue #4830) has no address lookup or API. The page
# states a single town-wide weekday for the smaller towns, which this source
# reads live. The larger towns have several collection days that depend on the
# street and are only published on a downloadable map, so for those the user
# selects their own collection day (read off that map) — the manual fallback.
#
# RECYCLING (yellow lid) is intentionally OMITTED. It runs fortnightly, but the
# fortnight phase/anchor is published ONLY as colour week-shading on the per-town
# map PDFs (even the single-round towns' calendars say "check the map"). There is
# no live, machine-readable anchor, and hardcoding one would rot. Only
# GENERAL_WASTE (red lid, weekly) is fully derivable.

URL = "https://www.isaac.qld.gov.au/residents/waste/kerbside-collection"

# Towns where the whole town shares ONE collection weekday in the page text.
# The values mirror the <h2> heading text on the page; parse() confirms the
# weekday live, these are only the selectable options for the config UI.
SINGLE_DAY_TOWNS = [
    "Coastal",
    "Glenden",
    "Middlemount",
    "Nebo",
]

# Towns with several collection days split by street (map-gated, no live feed):
# the user supplies their own collection day via the ``collection_day`` param.
MULTI_DAY_TOWNS = [
    "Clermont",
    "Dysart",
    "Moranbah",
]

ALL_TOWNS = SINGLE_DAY_TOWNS + MULTI_DAY_TOWNS

WEEKDAY_OPTIONS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# "<Town> has one bin collection day on a <Weekday>." The page sometimes uses a
# non-breaking space between "one" and "bin", so be tolerant of whitespace.
_SINGLE_DAY_RE = re.compile(
    r"has\s+one\s+bin\s+collection\s+day\s+on\s+an?\s+(\w+)",
    re.IGNORECASE,
)

# Roughly a year of weekly collections (52 weeks) projected forward from today.
_WEEKS_AHEAD = 52


def _town_weekdays(headings, source) -> dict[str, int | None]:
    """Map each single-day town to the weekday stated in its intro sentence.

    A user-supplied ``collection_day`` (the manual fallback for the multi-day
    towns, whose days are published only on a map) wins outright, so the table
    is then just the chosen town.
    """
    collection_day = source.params["collection_day"]
    if collection_day:
        return {source.params["town"]: recurrence.weekday(collection_day)}

    town_weekdays: dict[str, int | None] = {}
    for heading in headings:
        town = heading.get_text(" ", strip=True)
        if town not in SINGLE_DAY_TOWNS:
            continue
        # Read the first paragraph after the heading (the intro sentence),
        # stopping at the next town heading.
        intro = ""
        for sib in heading.find_all_next(["p", "h2"]):
            if sib.name == "h2":
                break
            intro = sib.get_text(" ", strip=True)
            break
        match = _SINGLE_DAY_RE.search(intro)
        if not match:
            continue
        weekday = recurrence.weekday(match.group(1))
        if weekday is not None:
            town_weekdays[town] = weekday
    return town_weekdays


def _describe(weekday, source):
    """Turn the resolved weekday into a weekly general-waste Schedule."""
    if weekday is None:
        return
    start = recurrence.next_weekday(weekday)
    yield Schedule("general waste", start, recurrence.WEEKLY, _WEEKS_AHEAD)


@final
class Source(BaseSource):
    TITLE = "Isaac Regional Council"
    DESCRIPTION = (
        "Source for Isaac Regional Council, Queensland, Australia "
        "(general waste, weekly)."
    )
    URL = URL
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    API_URL = URL

    TEST_CASES: ClassVar[dict] = {
        "Glenden (single-day town)": {"town": "Glenden"},
        "Middlemount (single-day town)": {"town": "Middlemount"},
        "Moranbah (multi-day, manual day)": {
            "town": "Moranbah",
            "collection_day": "Wednesday",
        },
    }

    PARAMS = (
        dropdown("town", ALL_TOWNS, label="Town"),
        dropdown(
            "collection_day", WEEKDAY_OPTIONS, label="Collection day", optional=True
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your town. The smaller towns (Coastal, Glenden, Middlemount, "
            "Nebo) have a single town-wide collection day, read automatically. "
            "The larger towns (Clermont, Dysart, Moranbah) have several days that "
            "depend on your street: look your day up on the council's collection "
            "map and select it in 'Collection day'. Only the weekly general waste "
            "(red lid) collection is provided; the fortnightly recycling phase is "
            "map-only and not available as a live feed."
        ),
    }

    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]

    REGIONS: ClassVar[list] = [
        region(f"Isaac Regional Council ({town})", url=URL, town=town)
        for town in SINGLE_DAY_TOWNS
    ]

    parse = parsers.HtmlParser("h2")

    preprocess = Compose(
        ArgumentLookup(_town_weekdays, argument="town"),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(type_value_map={"general waste": GENERAL_WASTE})

    def __init__(self, town: str, collection_day: str | None = None):
        super().__init__(town=town, collection_day=collection_day)
        if town in MULTI_DAY_TOWNS and not collection_day:
            raise SourceArgumentRequired(
                "collection_day",
                f"{town} has several collection days that depend on your street; "
                "look yours up on the council collection map and select it.",
            )
