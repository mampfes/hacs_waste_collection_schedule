from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, text_field
from waste_collection_schedule.preprocessors import (
    ArgumentLookup,
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Demonstrates: a council page that lists suburbs under a collection-weekday
# heading (no dates published). ArgumentLookup resolves the suburb to its
# weekday; RecurrenceExpander projects FOGO weekly and recycling / general waste
# on alternating ISO weeks, the recycling parity being a user setting.

COLLECTION_URL = (
    "https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/"
    "bin-collection-residential-and-commercial"
)

# Roughly half a year of weekly collections, as before the migration.
_WEEKS_AHEAD = 26


def _suburb_weekdays(items, source) -> dict[str, int]:
    """Map each suburb listed on the page to the weekday of its accordion."""
    table: dict[str, int] = {}
    for item in items:
        button = item.select_one(".accordion-button")
        if button is None:
            continue
        words = button.get_text(strip=True).split()
        weekday = recurrence.weekday(words[0]) if words else None
        if weekday is None:
            continue
        for li in item.select("li"):
            table.setdefault(li.get_text(strip=True), weekday)
    return table


def _describe(weekday, source):
    """FOGO weekly; recycling and general waste on opposite ISO-week parities."""
    start = recurrence.next_weekday(weekday)
    recycling_even = source.params["recycling_in_even_week"]
    yield Schedule("FOGO", start, recurrence.WEEKLY, _WEEKS_AHEAD)
    yield Schedule(
        "Recycling",
        start,
        recurrence.WEEKLY,
        _WEEKS_AHEAD,
        iso_week_parity="even" if recycling_even else "odd",
    )
    yield Schedule(
        "General Waste",
        start,
        recurrence.WEEKLY,
        _WEEKS_AHEAD,
        iso_week_parity="odd" if recycling_even else "even",
    )


@final
class Source(BaseSource):
    TITLE = "Shire of Harvey"
    DESCRIPTION = "Source for Shire of Harvey (WA) waste collection."
    URL = "https://www.harvey.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Australind (south of Paris Road)": {
            "suburb": "Australind (south of Paris Road)",
            "recycling_in_even_week": True,
        },
        "Harvey (east of railway)": {
            "suburb": "Harvey (east of railway to Highway including Weir Road)",
            "recycling_in_even_week": False,
        },
        "Roelands": {
            "suburb": "Roelands including Raymond Road",
            "recycling_in_even_week": True,
        },
    }

    PARAMS = (
        text_field("suburb", "Suburb / Collection Area"),
        boolean(
            "recycling_in_even_week",
            "Recycling collected on even ISO weeks",
            default=True,
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.harvey.wa.gov.au/services/rubbish-and-waste-services/"
            "bin-collection-residential-and-commercial and find your suburb in the "
            "collection day list. Use the exact text shown, e.g. 'Yarloop' or "
            "'Australind (south of Paris Road)'. "
            "For recycling_in_even_week: check your last recycling collection date "
            "and see if its ISO week number (https://whatweekisit.org/) was even "
            "(True) or odd (False)."
        ),
    }

    retrieve = HttpGetRetriever(url=COLLECTION_URL)
    parse = parsers.HtmlParser(".accordion-item")
    preprocess = Compose(
        ArgumentLookup(_suburb_weekdays, argument="suburb"),
        RecurrenceExpander(_describe),
    )
    transform = ICSTransformer(
        type_value_map={
            "FOGO": wt.ORGANIC,
            "Recycling": wt.RECYCLABLES,
            "General Waste": wt.GENERAL_WASTE,
        }
    )
