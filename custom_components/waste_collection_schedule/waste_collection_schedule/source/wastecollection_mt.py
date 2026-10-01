import re
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Request
from waste_collection_schedule.transformers import ICSTransformer

_TYPE_MAP = {
    "Mixed waste (black bag)": wt.GENERAL_WASTE,
    "Organic waste (white bag)": wt.ORGANIC,
    "Recycled waste (Grey or green bag)": wt.RECYCLABLES,
    "glass bottles": wt.GLASS,
}

_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "last": -1}
_FLOWTEXT = re.compile(r"^The collection of (?P<label>.+?) will\b(?P<rest>.*)", re.I)
_WEEKS = 53
_MONTHS = 12


def _rows(records, source):
    """One ``(date, label)`` row per collection the page's paragraphs announce.

    Two forms: "<b>Tuesday:</b> Mixed waste (black bag)" (every week) and
    "The collection of glass bottles will be carried out on every first and
    third Friday of the month." (monthly, on the named weeks).
    """
    for p in records:
        strong = p.find("strong")
        if strong:
            weekday = recurrence.weekday(strong.get_text().strip().strip(":"))
            _, _, label = p.get_text().partition(":")
            label = label.replace(" only", "").strip()
            if weekday is None or not label:
                continue
            for day in recurrence.recurring(
                recurrence.next_weekday(weekday), recurrence.WEEKLY, _WEEKS
            ):
                yield day, label
            continue
        found = _FLOWTEXT.match(p.get_text().strip())
        if not found or found["label"].lower().startswith("times"):
            continue
        words = re.findall(r"[a-z]+", found["rest"].lower())
        weekday = next(
            (w for w in map(recurrence.weekday, words) if w is not None), None
        )
        weeks = [_ORDINALS[w] for w in words if w in _ORDINALS]
        label = found["label"].replace(" only", "").strip()
        if weekday is None:
            continue
        for n in weeks:
            for day in recurrence.monthly_nth_weekdays(weekday, n, _MONTHS):
                yield day, label


@final
class Source(BaseSource):
    TITLE = "Malta"
    DESCRIPTION = "Nation wide collection schedule for Malta"
    URL = "https://www.wastecollection.mt/"
    COUNTRY = "mt"

    TEST_CASES: ClassVar[dict] = {"test": {}}

    PARAMS = ()

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    retrieve = Request("https://www.wastecollection.mt/")
    parse = HtmlParser("p")
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
