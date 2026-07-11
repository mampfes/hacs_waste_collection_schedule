import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

# Three collection columns share one value shape family: either
# "Fortnightly/Weekly on Thursday, Next: 23 Jul 2026" (an explicit next
# date) or a bare "Weekly on Thursdays" (no date, just a weekday name). The
# only source-specific code is _describe, which tells the two apart.
#
# Note: the "Food & Green Waste" caption is exposed under the IntraMaps
# *column* "Garden Waste" - keying on the caption (as the legacy source's
# name-based lookup happened to, coincidentally, still work) would be wrong
# in general; this source keys on column throughout.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://gis.bayside.vic.gov.au",
    instance="IntraMaps910",
    config_id="7a287c70-ea2d-4abd-943c-8bf55cf09fe5",
    project="1c8f869f-fa4a-4c39-b7bb-94641ee61597",
    module_id="5c590b56-e989-48a3-9bb8-207d4a388373",
)

# IntraMaps column name -> canonical waste type. "Bin Collection Day" and
# "Street Sweeping" are also present in the response but are not collection
# fields, so they are left out of this map (and therefore ignored).
_TYPE_MAP = {
    "Recycling": RECYCLABLES,
    "Domestic Waste": GENERAL_WASTE,
    "Garden Waste": ORGANIC,  # displayed to residents as "Food & Green Waste"
}

_NEXT_DATE_RE = re.compile(r"Next:\s*(\d{1,2}\s+\w+\s+\d{4})")
_WEEKLY_DAY_RE = re.compile(r"on\s+(\w+day)", re.IGNORECASE)


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    date_match = _NEXT_DATE_RE.search(text)
    if date_match:
        try:
            next_date = date_parsers.auto(date_match.group(1))
        except (ValueError, TypeError):
            return
        step = (
            recurrence.FORTNIGHTLY
            if "fortnightly" in text.lower()
            else recurrence.WEEKLY
        )
        yield Schedule(column, next_date, step, 13)
        return

    if "weekly" in text.lower():
        day_match = _WEEKLY_DAY_RE.search(text)
        if day_match:
            weekday = recurrence.weekday(day_match.group(1))
            if weekday is not None:
                yield Schedule(
                    column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26
                )


@final
class Source(BaseSource):
    TITLE = "Bayside Council (Victoria)"
    DESCRIPTION = "Source for Bayside Council rubbish collection."
    URL = "https://bayside.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "76 Royal Avenue Sandringham": {
            "street_address": "76 Royal Avenue Sandringham"
        },
    }

    PARAMS = (text_field("street_address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": ("Enter your street address including suburb."),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="street_address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, street_address: str):
        super().__init__(street_address=street_address)
