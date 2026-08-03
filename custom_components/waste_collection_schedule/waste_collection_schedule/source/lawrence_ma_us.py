import re
from collections.abc import Iterable
from typing import ClassVar, final

from waste_collection_schedule import lookups, parsers, recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Demonstrates: a weekday-list scrape resolved by preprocessors.ArgumentLookup
# and projected into a recurring weekly schedule.
#
# The City of Lawrence publishes its curbside collection schedule as five
# weekday tabs (Monday-Friday). Each tab lists the streets collected that
# weekday. Trash and single-stream recycling are collected together on the
# resident's regular weekday, so each matched weekday emits a weekly trash
# schedule and a weekly recycling schedule.
#
# The streets are in the delivered HTML (a CivicPlus tabbed widget), so a plain
# GET plus an HtmlParser is enough; ArgumentLookup then matches the resident's
# street against the scraped table and lists the valid streets when it misses. A
# street may be listed on more than one weekday when it is split into segments
# (e.g. "Andover Street (State Street to Ballard Road)" on Monday and "Andover
# Street (State Street to Shawsheen Road)" on Tuesday); in that case every
# matching weekday is scheduled.

# Number of weekly occurrences to project per matched weekday (~6 months).
_WEEKS_AHEAD = 26


def _base_street(name: str) -> str:
    """Strip a trailing qualifier like '(State Street to Ballard Road)'."""
    return lookups.normalize_text(re.split(r"\s*\(", name, maxsplit=1)[0])


def _street_weekdays(panels, source) -> dict[str, list[int]]:
    """Map each street to the weekday panels listing it (Monday=0).

    The five panels render in weekday order Monday (0) to Friday (4).
    """
    weekdays: dict[str, list[int]] = {}
    for weekday, panel in enumerate(panels):
        for item in panel.select("ul li"):
            text = item.get_text(" ", strip=True)
            if not text:
                continue
            listed = weekdays.setdefault(_base_street(text).title(), [])
            if weekday not in listed:
                listed.append(weekday)
    return weekdays


def _describe(weekdays: list[int], source) -> Iterable[Schedule]:
    for weekday in weekdays:
        start = recurrence.next_weekday(weekday)
        yield Schedule("trash", start, recurrence.WEEKLY, _WEEKS_AHEAD)
        yield Schedule("recycling", start, recurrence.WEEKLY, _WEEKS_AHEAD)


@final
class Source(BaseSource):
    TITLE = "City of Lawrence"
    DESCRIPTION = "Source for City of Lawrence, Massachusetts, USA."
    URL = "https://www.cityoflawrence.com"
    COUNTRY = "us"

    API_URL = "https://www.cityoflawrence.com/161/Collection-Schedule"

    TEST_CASES: ClassVar[dict] = {
        "Monday street (Adams Street)": {"street": "Adams Street"},
        "Tuesday street (Bailey Street)": {"street": "Bailey Street"},
        "Friday street (Ames Street)": {"street": "Ames Street"},
    }

    PARAMS = (text_field("street", label="Street Name"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open the City of Lawrence collection schedule at "
            "https://www.cityoflawrence.com/161/Collection-Schedule and find "
            "your street on the Monday to Friday tabs. Enter the street name "
            "exactly as listed (for example 'Adams Street'). Omit any segment "
            "qualifier shown in brackets."
        ),
    }

    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]

    RAISE_ON_EMPTY = True

    retrieve = retrievers.HttpGetRetriever(url=API_URL)
    parse = parsers.HtmlParser("div.cpTabPanel")

    preprocess = Compose(
        ArgumentLookup(_street_weekdays, argument="street"),
        RecurrenceExpander(_describe),
    )

    transform = ICSTransformer(
        type_value_map={"trash": GENERAL_WASTE, "recycling": RECYCLABLES},
    )
