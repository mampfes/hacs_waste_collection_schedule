import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer

# The council's "Find my bin day" map returns free text per bin:
#   FOGO                "Monday (Weekly)"
#   General Waste       "Tuesday, Week 2 (13 Oct 2026)"
#   Recycling           "Tuesday, Week 1 (20 Oct 2026)"
# FOGO is weekly on its own weekday (which can differ from the other bins and
# is per address, not per area); General Waste and Recycling are fortnightly
# from the stated next date.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://subiaco.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="95fc31a6-7249-4e7f-81cd-342f8e977833",
    project="3ef9ed21-2b91-467a-a7c0-ca0da50db9e7",
    default_selection_layer="b5583c5c-337e-4ab1-8987-caad834d5016",
)

_TYPE_MAP = {
    "Day": wt.ORGANIC,
    "General Waste Collection Day": wt.GENERAL_WASTE,
    "Recycle Collection Day": wt.RECYCLABLES,
}

_DATE_RE = re.compile(r"\((\d{1,2}\s+\w+\s+\d{4})\)")
_WEEKDAY_RE = re.compile(r"^\s*(\w+)")


def _describe(record, source):
    column = record.get("column", "")
    if column not in _TYPE_MAP:
        return
    text = record.get("value", "").strip()
    if not text:
        return

    match = _DATE_RE.search(text)
    if match:  # "Tuesday, Week 2 (13 Oct 2026)" -> fortnightly from that date
        try:
            next_date = date_parsers.auto(match.group(1))
        except (ValueError, TypeError):
            return
        yield Schedule(column, next_date, recurrence.FORTNIGHTLY, 13)
        return

    match = _WEEKDAY_RE.match(text)  # "Monday (Weekly)" -> weekly
    if not match:
        return
    weekday = recurrence.weekday(match.group(1))
    if weekday is not None:
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26)


@final
class Source(BaseSource):
    TITLE = "City of Subiaco"
    DESCRIPTION = "Source for City of Subiaco, WA waste collection."
    URL = "https://www.subiaco.wa.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Barker Road Subiaco": {"address": "241 Barker Road SUBIACO"},
        "Hay Street Subiaco": {"address": "10 Hay Street SUBIACO"},
    }

    PARAMS = (street_address(),)

    WASTE_TYPES: ClassVar[list] = [wt.ORGANIC, wt.GENERAL_WASTE, wt.RECYCLABLES]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '241 Barker Road SUBIACO')."
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
