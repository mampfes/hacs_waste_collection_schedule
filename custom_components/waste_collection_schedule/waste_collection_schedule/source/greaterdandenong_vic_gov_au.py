from typing import ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntegrationClientConfig,
    IntegrationClientRetriever,
    IntegrationPanelParser,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Two-step Integration API flow (apikey search -> mapkey/dbkey -> details
# form). Waste day is a bare weekday name (weekly); Garden/Recycling carry an
# explicit "<weekday>, <date>" next-collection value (fortnightly); Street
# Sweep is a single explicit date. Street Sweep has no matching canonical
# waste type, so it is left out of the type map: the transformer preserves
# "Street Sweep" verbatim rather than forcing it into GENERAL_WASTE the way
# the legacy ICON_MAP did. The only source-specific code is _describe, which
# tells the columns apart and reads each one's date/cadence.

INTRAMAPS_CONFIG = IntegrationClientConfig(
    base_url="https://maps.greaterdandenong.com",
    instance="IntraMaps21B",
    api_key="05dbdab3-8568-4d7e-83e0-22cc06a09f7f",
)

SEARCH_FORM = "35f43a60-983b-4c11-ac56-8b1d10e8389f"
DETAILS_FORM = "1ee8052a-e624-45c6-8aee-a2bb990f6a8c"

_WEEKLY_COLUMN = "waste_day"
_FORTNIGHTLY_COLUMNS = {"garden_day", "recycle_day"}
_SINGLE_COLUMN = "street_sweep"

_TYPE_MAP = {
    _WEEKLY_COLUMN: GENERAL_WASTE,
    "garden_day": GARDEN_WASTE,
    "recycle_day": RECYCLABLES,
}

_SWEEP_DATE_FORMAT = date_parsers.for_format("%d %B %Y")


def _describe(record, source):
    column = record.get("column", "")
    text = record.get("value", "").strip()
    if not text:
        return

    if column == _WEEKLY_COLUMN:
        weekday = recurrence.weekday(text)
        if weekday is None:
            return
        yield Schedule(column, recurrence.next_weekday(weekday), recurrence.WEEKLY, 13)
        return

    if column in _FORTNIGHTLY_COLUMNS:
        # e.g. "Wednesday, 17 July 2026" -- the date is the part after the comma.
        try:
            start = date_parsers.auto(text.split(", ", 1)[1])
        except (ValueError, TypeError, IndexError):
            return
        yield Schedule(column, start, recurrence.FORTNIGHTLY, 13)
        return

    if column == _SINGLE_COLUMN:
        try:
            event_date = _SWEEP_DATE_FORMAT(text)
        except (ValueError, TypeError):
            return
        # Distinct, readable label; not in _TYPE_MAP so the transformer
        # preserves "Street Sweep" rather than resolving/forcing a type.
        yield Schedule("Street Sweep", event_date, count=1)


@final
class Source(BaseSource):
    TITLE = "Greater Dandenong City Council"
    DESCRIPTION = "Source for greaterdandenong.vic.gov.au waste collection."
    URL = "https://www.greaterdandenong.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "45 Ardgower Road Noble Park": {"address": "45 Ardgower Road Noble Park"},
        "8 Foster Street Dandenong": {"address": "8 Foster Street Dandenong"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as it appears on the "
            "<a href='https://www.greaterdandenong.vic.gov.au/find-my-bin-day'>"
            "Find My Bin Day</a> page."
        ),
    }

    retrieve = IntegrationClientRetriever(
        INTRAMAPS_CONFIG,
        search_form=SEARCH_FORM,
        details_form=DETAILS_FORM,
        address="address",
    )
    parse = IntegrationPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
