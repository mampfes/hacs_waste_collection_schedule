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

# General waste is a bare "Every Friday" (weekly). Recycling is published as
# a single explicit next-pickup date with no cadence, so it is emitted as one
# occurrence rather than expanded - preserving the legacy source's behaviour
# of returning exactly the one date the provider gives.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://cosp.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="29b80b8c-2c27-4a14-8f10-678c7947f7be",
    project="cf285c38-0d67-406e-93c2-35ae3d066521",
)

# IntraMaps column name -> canonical waste type.
_TYPE_MAP = {
    "bin_day": GENERAL_WASTE,
    "recycling_day": RECYCLABLES,
}

# The recycling value is free text such as "17 July 2026"; pull out just the
# date rather than parsing the whole string, in case the provider prefixes it
# with wording dateutil can't handle unaided.
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    if column == "bin_day":
        match = re.match(r"every\s+(\w+)", text.lower())  # "Every Friday" -> weekly
        if not match:
            return
        weekday = recurrence.weekday(match.group(1))
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)
        return

    # recycling_day: a single explicit date, not a recurring cadence.
    match = _DATE_RE.search(text)
    if not match:
        return
    try:
        next_date = date_parsers.auto(match.group(1))
    except (ValueError, TypeError):
        return
    yield Schedule(column, next_date, recurrence.WEEKLY, 1)


@final
class Source(BaseSource):
    TITLE = "City of South Perth"
    DESCRIPTION = "Source for City of South Perth waste collection."
    URL = "https://southperth.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Lansdowne Road": {"address": "156 Lansdowne Road KENSINGTON"},
        "Roebuck Drive": {"address": "13 Roebuck Drive"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '156 Lansdowne Road KENSINGTON')."
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
