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

# Two value-text cadences on one council: FOGO is a bare "Every Friday"
# (weekly); General Waste and Recycling are "Friday - 24 July 2026"
# (fortnightly with an explicit next date). The only source-specific code is
# _describe, which tells the two shapes apart per column.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://bayswater.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="359e0f03-92e0-4309-9024-f199f434a742",
    project="3c55e04f-d94e-4735-aecf-2e62b40bfd52",
    lite_config_id="221746d2-92cc-4591-a2da-bbecd930bb1b",
    module_id="d1e90488-605a-43ad-88cd-793e0a7d7c4e",
)

# IntraMaps column name -> canonical waste type. One map: selects the
# collection fields (others ignored) and types them.
_TYPE_MAP = {
    "FOGO_Green_Lid": ORGANIC,
    "General_Waste_Red_Lid": GENERAL_WASTE,
    "Recycling_Yellow_Lid": RECYCLABLES,
}

# Values are free text such as "Friday - 24 July 2026"; pull out just the
# date rather than parsing the whole string, so incidental wording can't
# derail it.
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    match = re.match(r"every\s+(\w+)", text.lower())  # "Every Friday" -> weekly
    if match:
        weekday = recurrence.weekday(match.group(1))
        if weekday is not None:
            yield Schedule(
                column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26
            )
        return

    match = _DATE_RE.search(text)  # "Friday - 24 July 2026" -> fortnightly
    if not match:
        return
    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return
    yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)


@final
class Source(BaseSource):
    TITLE = "City of Bayswater"
    DESCRIPTION = "Source for City of Bayswater waste collection."
    URL = "https://www.bayswater.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Wholley St Bayswater": {"address": "9 Wholley St Bayswater"},
        "Ivory St Noranda": {"address": "14 Ivory St Noranda"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '9 Wholley St Bayswater')."
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
