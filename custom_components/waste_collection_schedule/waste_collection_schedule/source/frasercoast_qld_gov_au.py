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
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# "Bin Day" is a bare weekday name (weekly general waste); "Recycling Day" is
# fortnightly with an explicit "Next: <date>" marker. The only source-specific
# code is _describe, which tells the two columns apart.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://fcrc.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="e003842b-3af0-44a7-8bd8-45f9880f2c30",
    project="95d8904e-e9ef-4cac-88b5-def885f74f4d",
    lite_config_id="3727d4c0-1e2e-4eff-9669-b89f3a1919fe",
    module_id="b4b2af30-9b10-41a9-b9c9-3e253e2563a1",
    selection_layer_filter="93ccc583-6119-435f-845e-33deae245002",
    default_selection_layer="93ccc583-6119-435f-845e-33deae245002",
)

# IntraMaps column name -> canonical waste type.
_TYPE_MAP = {
    "Bin Day": GENERAL_WASTE,
    "Recycling Day": RECYCLABLES,
}

# The recycling value is free text such as "Thursday Week A; Next: 23 Jul
# 2026"; pull out just the "Next:" date rather than parsing the whole string.
_NEXT_DATE_RE = re.compile(r"Next:\s*(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    if column == "Bin Day":
        weekday = recurrence.weekday(text)  # bare weekday name -> weekly
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)
        return

    match = _NEXT_DATE_RE.search(text)
    if not match:
        return
    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return
    yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)


@final
class Source(BaseSource):
    TITLE = "Fraser Coast Regional Council"
    DESCRIPTION = "Source for Fraser Coast Regional Council waste collection."
    URL = "https://www.frasercoast.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Arbornine Road Glenwood": {"address": "57 Arbornine Road Glenwood"},
        "Tavistock Street Torquay": {"address": "77 Tavistock Street Torquay"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '57 Arbornine Road Glenwood'). "
            "Search at https://www.frasercoast.qld.gov.au/Services/"
            "Online-Services/Check-your-bin-day"
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
