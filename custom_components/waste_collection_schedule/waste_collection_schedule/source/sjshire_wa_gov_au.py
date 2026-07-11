from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntegrationClientConfig,
    IntegrationClientRetriever,
    IntegrationPanelParser,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Multiple addresses can share a street/suburb combination, so the search step
# fetches every candidate (match_field="Address") and the retriever picks the
# exact one, raising suggestions otherwise -- IntegrationClientRetriever's
# generic disambiguation, not source-specific code. Rubbish is a bare weekday
# name (weekly); Recycling is worded "<day> this/next week" (fortnightly).
#
# The legacy source took a non-standard `predict` argument that limited the
# result to a single upcoming occurrence unless the caller asked for more.
# That is exactly the time-windowing this project's framework owns, not a
# source: dropped here, and the pipeline always returns the full recurring
# series (see doc/contributing_source.md, "Empty results and exceptions").

INTRAMAPS_CONFIG = IntegrationClientConfig(
    base_url="https://maps.sjshire.wa.gov.au",
    instance="IntraMaps22B",
    api_key="58383723-1396-43cc-a5cf-722e786208c6",
)

SEARCH_FORM = "de2aecaf-1e4d-4d25-8146-b0f0109aa458"
DETAILS_FORM = "a51626b7-3892-44f4-9fba-b0264486bda5"

_TYPE_MAP = {
    "WasteCollectionDay": GENERAL_WASTE,
    "RecycleDay": RECYCLABLES,
}


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
    parts = text.split()
    if not parts:
        return
    weekday = recurrence.weekday(parts[0])
    if weekday is None:
        return
    start = _this_or_next_week(weekday, "next" in text)
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

    retrieve = IntegrationClientRetriever(
        INTRAMAPS_CONFIG,
        search_form=SEARCH_FORM,
        details_form=DETAILS_FORM,
        address="address",
        match_field="Address",
    )
    parse = IntegrationPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
