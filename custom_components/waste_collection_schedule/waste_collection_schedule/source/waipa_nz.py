import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.recurrence import WEEKLY
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GLASS, RECYCLABLES

# Waipa publishes several explicit dates per field rather than a cadence
# (e.g. "Will be collected on 15-Jul-2026, and then ... on 29-Jul-2026"), so
# there is no recurrence to project: _describe just regexes every date out of
# the matching column's text and yields one single-occurrence Schedule per
# date. The "Mixed Recycling" / "Glass Recycling" columns are matched by
# substring (their full column text is the long verbose caption, e.g.
# "Mixed Recycling (YELLOW bin - Plastic 1 2 5, Paper, Cardboard, Cans):"),
# still keyed on ``column`` rather than a separate caption field.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://waipadc.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="6aa41407-1db8-44e1-8487-0b9a08965283",
    project="b5bc138e-edce-4b01-b159-ec44539ab455",
    module_id="5373c4e1-c975-4c8f-b51a-0ac976f5313c",
    default_selection_layer="e7163a17-2f10-42b1-8dbf-8c53adf089a8",
)

# Internal schedule keys -> canonical waste type (decoupled from the verbose
# IntraMaps column text so the transformer's map stays short and stable).
_TYPE_MAP = {
    "recycling": RECYCLABLES,
    "glass": GLASS,
}

_RECYCLING_COLUMN_RE = re.compile(r"Mixed Recycling", re.IGNORECASE)
_GLASS_COLUMN_RE = re.compile(r"Glass Recycling", re.IGNORECASE)

# Extract dates in format "DD-Mon-YYYY".
_DATE_RE = re.compile(r"\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b")
_parse_date = date_parsers.for_format("%d-%b-%Y")


def _describe(record, source):
    column = record.get("column", "")
    if _RECYCLING_COLUMN_RE.search(column):
        key = "recycling"
    elif _GLASS_COLUMN_RE.search(column):
        key = "glass"
    else:
        return

    text = record.get("value", "")
    for date_str in _DATE_RE.findall(text):
        try:
            collection_date = _parse_date(date_str)
        except (ValueError, TypeError):
            continue
        yield Schedule(key, collection_date, WEEKLY, 1)


@final
class Source(BaseSource):
    TITLE = "Waipa District Council"
    DESCRIPTION = "Source for Waipa District Council. Finds both general and glass recycling dates."
    URL = "https://www.waipadc.govt.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "10 Queen Street": {"address": "10 Queen Street"},  # Monday
        "1 Acacia Avenue": {"address": "1 Acacia Avenue"},  # Wednesday
    }

    PARAMS = (text_field("address", "Street Address"),)

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
