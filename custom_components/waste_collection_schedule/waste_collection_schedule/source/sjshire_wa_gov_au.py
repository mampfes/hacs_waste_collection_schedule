import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# The shire moved its map off the self-hosted maps.sjshire.wa.gov.au IntraMaps
# server onto TechnologyOne's SaaS platform (ser.spatial.t1cloud.com). The old
# apikey Integration API is gone (it now serves the MapBuilder HTML shell, hence
# the JSONDecodeError), so this uses the stateful session handshake the sibling
# WA councils on the same platform use (IntraMapsRetriever + MapsClientConfig,
# see kwinana_wa_gov_au.py). The infoPanels field names are unchanged:
# WasteCollectionDay is a bare weekday (weekly); RecycleDay is worded
# "<day> this/next week" (fortnightly).
#
# The legacy source took a non-standard `predict` argument that limited the
# result to a single upcoming occurrence unless the caller asked for more.
# That is exactly the time-windowing this project's framework owns, not a
# source: dropped here, and the pipeline always returns the full recurring
# series (see doc/contributing_source.md, "Empty results and exceptions").

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://ser.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="93074f9e-ef2a-49d5-9866-91422949b9da",
    project="2e3adc22-b61d-4548-92d1-c1b02f9a30a3",
    module_id="bd33efd3-682b-478f-9dd1-82bdad11b52d",
)

_TYPE_MAP = {
    "WasteCollectionDay": GENERAL_WASTE,
    "RecycleDay": RECYCLABLES,
}

# RecycleDay reads "<day> this/next week", but the "this week" variant arrives
# with the day and "this" run together ("MondayThis Week") while "next week"
# keeps the space ("Tuesday Next Week"); strip the suffix either way.
_RECYCLE_SUFFIX = re.compile(r"\s*(?:this|next)\s*week\s*$")


def _this_or_next_week(weekday: int, next_week: bool) -> date:
    """Resolve "<day> this/next week" to a date: that week's Monday + offset.

    Matches the wording literally rather than resolving to the next upcoming
    occurrence: if the named day within "this week" has already passed, the
    result is that (past) date, same as the legacy source and the council's
    own site.
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    target = week_start + timedelta(days=weekday)
    if next_week:
        target += timedelta(days=7)
    return target


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip().lower()
    if not text:
        return

    if column == "WasteCollectionDay":
        weekday = recurrence.weekday(text)
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)
        return

    # column == "RecycleDay": "<day> this/next week"
    next_week = "next" in text
    day = _RECYCLE_SUFFIX.sub("", text).strip()
    weekday = recurrence.weekday(day)
    if weekday is None:
        return
    start = _this_or_next_week(weekday, next_week)
    yield Schedule(column, start, recurrence.FORTNIGHTLY, 13)


@final
class Source(BaseSource):
    TITLE = "Shire of Serpentine Jarrahdale"
    DESCRIPTION = "Source for www.sjshire.wa.gov.au Waste Collection Services"
    URL = "https://www.sjshire.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday": {"address": "5 Pingaring Court BYFORD WA 6122"},
        "Tuesday": {"address": "865 South Western Highway BYFORD WA 6122"},
        "Wednesday": {"address": "701 Jarrahdale Road JARRAHDALE WA 6124"},
        "Thursday": {"address": "6 Paterson Street MUNDIJONG WA 6123"},
        "Friday": {"address": "1548 Kargotich Road MARDELLA WA 6125"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
