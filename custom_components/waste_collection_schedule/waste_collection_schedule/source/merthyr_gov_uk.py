import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a provider that publishes a recurring pattern rather than dates.
# The council's postcode finder answers with a weekday per stream and, for
# household and garden waste, "week one" or "week two", plus which of the two
# it currently is. _describe() reads that wording into Schedules (the only
# source-specific part); RecurrenceExpander projects them and the week label is
# mapped onto an ISO-week parity, so the alternation stays right across
# 53-week years.

_RULE = re.compile(
    r"Your (recycling|household waste|garden waste) collection day is (\w+)"
    r"(?: every week| in week (one|two))",
    re.I,
)
_THIS_WEEK = re.compile(r"This is week (one|two)", re.I)
_WEEK_NUMBER = {"one": 1, "two": 2}


def _describe(record, source):
    text = re.sub(r"\s+", " ", record.get_text(" "))
    current = _THIS_WEEK.search(text)
    if current is None:
        return
    today = datetime.date.today()
    today_is_even = today.isocalendar().week % 2 == 0
    this_week = _WEEK_NUMBER[current.group(1).lower()]

    for stream, day, week in _RULE.findall(text):
        weekday = recurrence.weekday(day)
        if weekday is None:
            continue
        parity = None
        if week:
            # Week `n` has the same ISO parity as today when it is the current
            # week, the opposite parity otherwise.
            even = today_is_even == (_WEEK_NUMBER[week.lower()] == this_week)
            parity = "even" if even else "odd"
        yield Schedule(
            stream.lower(),
            recurrence.next_weekday(weekday),
            recurrence.WEEKLY,
            52,
            iso_week_parity=parity,
        )


@final
class Source(BaseSource):
    TITLE = "Merthyr Tydfil County Borough Council"
    DESCRIPTION = "Source for Merthyr Tydfil County Borough Council waste collections."
    URL = "https://www.merthyr.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "CF47 0AA": {"postcode": "CF47 0AA"},
        "CF47 9AA": {"postcode": "CF47 9AA"},
        "CF48 1AA": {"postcode": "CF48 1AA"},
    }

    PARAMS = (postcode(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode as on the council's collection day page: "
            "https://www.merthyr.gov.uk/resident/bins-and-recycling/check-your-collection-day/ "
            "If the page reports no results, the postcode is not currently "
            "supported by the council's finder."
        ),
    }

    retrieve = retrievers.HttpPostRetriever(
        "https://www.merthyr.gov.uk/umbraco/Surface/BinDaySurface/GetCollectionDay",
        data=lambda postcode=None, **_: {"postcode": postcode},
    )

    parse = parsers.ArgumentGuard(
        parsers.HtmlParser("div.collection-results"),
        argument="postcode",
        contains="Collection days for",
        hint="the council's finder reports no results for this postcode",
    )

    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(
        type_value_map={
            "household waste": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden waste": wt.GARDEN_WASTE,
        },
    )
