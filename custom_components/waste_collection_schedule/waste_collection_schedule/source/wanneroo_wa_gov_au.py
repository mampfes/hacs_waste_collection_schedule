import re
from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntegrationWidgetConfig,
    IntegrationWidgetRetriever,
    IntraMapsPanelParser,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# The council embeds IntraMaps' own bin-lookup widget rather than publishing a
# static Integration API config, so there is no MapsClientConfig to declare:
# the api key, form id, config id and project name rotate and are scraped from
# the widget script on every fetch. That whole flow (scrape -> search ->
# MapBuilder session -> Integration/set selection) is the shared
# IntegrationWidgetRetriever, and it hands back the same raw infoPanels dict
# IntraMapsPanelParser reads for every other IntraMaps council.
#
# The cadence ("General Bin -THURSDAY NEXT Week", "Greens Bin - MONDAY Week
# AFTER NEXT") is embedded in each field's value rather than a caption, so
# _describe (the only source-specific code left) is what tells the bin type and
# cadence apart.

INTRAMAPS_CONFIG = IntegrationWidgetConfig(
    page_url="https://www.wanneroo.wa.gov.au/bincollections",
    base_url="https://wanneroo.spatial.t1cloud.com",
    instance="spatial/intramaps",
    map_project="4c19a56b-7a9e-437b-a3f1-a584aa3184fd",
    map_module="aae4bf39-9508-4528-9436-5942a23ddd7a",
)

# Bin-type label -> canonical waste type. Each IntraMaps column
# (General_Waste_Day, Recycling_Day, Go_Green_Bin_Day) already carries a
# value combining a bin-type phrase and the cadence ("General Bin -THURSDAY
# NEXT Week"), so the label _describe derives from that phrase (mirroring the
# legacy source's own keyword rules) is the map's key.
_TYPE_MAP = {
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "Garden Organics": GARDEN_WASTE,
}

_THIS_NEXT_WEEK_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(this|next)\s+week"
)
_WEEK_AFTER_NEXT_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+week\s+after\s+next"
)
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _bin_type_label(bin_type_raw: str) -> str:
    lowered = bin_type_raw.lower()
    if "general" in lowered:
        return "General Waste"
    if "recycl" in lowered:
        return "Recycling"
    if "green" in lowered or "garden" in lowered:
        return "Garden Organics"
    return bin_type_raw


def _describe(record, source):
    column = record.get("column") or ""
    if not column.lower().endswith("day"):
        return
    raw = record.get("value") or ""
    if "-" not in raw:
        return

    bin_type_raw, rhythm = raw.split("-", 1)
    bin_type_raw = bin_type_raw.strip()
    rhythm = rhythm.strip()
    label = _bin_type_label(bin_type_raw)
    rhythm_lower = rhythm.lower()

    match = _THIS_NEXT_WEEK_RE.search(rhythm_lower)
    if match:
        weekday = recurrence.weekday(match.group(1))
        if weekday is None:
            return
        # General waste is weekly; recycling/garden organics are fortnightly.
        step = (
            recurrence.WEEKLY
            if "general" in bin_type_raw.lower()
            else recurrence.FORTNIGHTLY
        )
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        start = week_start + timedelta(days=weekday)
        if match.group(2) == "next":
            start += timedelta(days=7)
        yield Schedule(label, start, step, 10)
        return

    match = _WEEK_AFTER_NEXT_RE.search(rhythm_lower)
    if match:
        weekday = recurrence.weekday(match.group(1))
        if weekday is None:
            return
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        start = week_start + timedelta(days=weekday) + timedelta(days=14)
        yield Schedule(label, start, recurrence.FORTNIGHTLY, 10)
        return

    weekday = recurrence.weekday(rhythm_lower)
    if weekday is not None:
        yield Schedule(label, recurrence.next_weekday(weekday), recurrence.WEEKLY, 20)
        return

    if rhythm_lower.startswith("fortnightly"):
        date_match = _DATE_RE.search(rhythm)
        if not date_match:
            return
        try:
            start = date_parsers.auto(date_match.group(1))
        except (ValueError, TypeError):
            return
        yield Schedule(label, start, recurrence.FORTNIGHTLY, 10)


@final
class Source(BaseSource):
    TITLE = "City of Wanneroo"
    DESCRIPTION = "Source for City of Wanneroo."
    URL = "https://www.wanneroo.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "23 Bakana LP LANDSDALE": {"address": "23 Bakana LP LANDSDALE"},
        "13/26 Princeton CIR ALEXANDER HEIGHTS": {
            "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
        },
        "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '23 Bakana LP LANDSDALE')."
        ),
    }

    retrieve = IntegrationWidgetRetriever(INTRAMAPS_CONFIG)
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)
