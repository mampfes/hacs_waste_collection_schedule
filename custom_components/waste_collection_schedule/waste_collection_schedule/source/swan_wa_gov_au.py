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

# Simplest IntraMaps shape: every collection is fortnightly with an explicit
# "next date" value, keyed by column (IntraMapsRetriever + IntraMapsPanelParser
# handle the stateful session handshake and field extraction). The only
# source-specific code is _describe, which parses the free-text date out of
# each column's value; a non-date placeholder (e.g. a future FOGO rollout
# notice) simply fails to parse and is skipped, matching the live provider.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://swan.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="4c6eefa0-c035-40d1-b553-be6e06446b38",
    project="41a8ffbd-0da0-47c9-9957-b0dcb8a1bfc3",
    module_id="5a0205e5-ab05-4d94-a97f-2ae565ae48ff",
    selection_layer_filter="efd1a218-d9c4-43ec-b1bb-17514d03c3a3",
    default_selection_layer="efd1a218-d9c4-43ec-b1bb-17514d03c3a3",
)

# IntraMaps column name -> canonical waste type. One map: selects the
# collection fields (others ignored) and types them.
_TYPE_MAP = {
    "Next_General_Waste_Collection": GENERAL_WASTE,
    "Next_Recycling_Collection": RECYCLABLES,
    "Next_FOGO_Collection": ORGANIC,
}

# Values are free text such as "Friday, 17 July 2026"; pull out just the date
# rather than parsing the whole string, so incidental wording (or a
# non-date placeholder, e.g. a future FOGO rollout notice) can't derail it.
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return

    match = _DATE_RE.search(record.get("value", ""))
    if not match:
        return

    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return

    yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)


@final
class Source(BaseSource):
    TITLE = "City of Swan"
    DESCRIPTION = "Source for City of Swan waste collection."
    URL = "https://www.swan.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Stratton": {"address": "34 Oldenburg Pass Stratton"},
        "Midland": {"address": "307 Great Eastern Highway Midland"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '34 Oldenburg Pass Stratton'). "
            "Search at https://www.swan.wa.gov.au/waste-and-sustainability/"
            "waste-and-recycling-services/bins/find-my-bin-day"
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
