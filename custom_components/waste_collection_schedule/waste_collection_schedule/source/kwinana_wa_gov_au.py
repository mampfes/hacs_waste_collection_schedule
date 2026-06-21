import datetime
import re
from typing import final

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import (
    IntraMapsPanelParser,
    IntraMapsRetriever,
    MapsClientConfig,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Demonstrates: a stateful-session service (IntraMapsRetriever + IntraMapsPanelParser)
# plus the reusable RecurrenceExpander preprocessor. The only source-specific code
# is _describe(), which parses Kwinana's recurrence wording ("Every Friday",
# "Friday Next Week") into a Schedule; the expander projects it and a plain
# ICSTransformer types each row by its IntraMaps column.

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://kwinana.spatial.t1cloud.com",
    instance="spatial/intramaps",
    config_id="361cf79c-756a-4c28-903a-a8ed0347cacb",
    project="139a0e2d-fa83-4232-86e9-5e29f342e289",
    lite_config_id="96651193-ca0f-4797-95d7-98e972248fad",
    module_id="cbd33a46-14e5-4ca2-9009-03a51dcbc889",
    selection_layer_filter="c6352192-20e8-402c-85c1-ca8515d3cae3",
    default_selection_layer="c6352192-20e8-402c-85c1-ca8515d3cae3",
)

# IntraMaps column name -> canonical waste type. One map: selects the collection
# fields (others ignored) and types them.
_TYPE_MAP = {
    "Rubbish_Collection_Day": GENERAL_WASTE,
    "Recycle_Collection": RECYCLABLES,
    "Garden Organics Collection": GARDEN_WASTE,
}


def _phrase_to_schedule(text: str, key: str) -> Schedule | None:
    """Parse Kwinana's recurrence wording into a Schedule (source-specific)."""
    normalised = text.strip().lower()

    match = re.match(r"every\s+(\w+)", normalised)  # "Every Friday" -> weekly
    if match:
        weekday = recurrence.WEEKDAYS.get(match.group(1))
        if weekday is not None:
            return Schedule(
                key, recurrence.next_weekday(weekday), recurrence.WEEKLY, 26
            )

    # "Friday This Week" / "Friday Next Week" -> fortnightly
    match = re.match(r"(\w+)\s+(this|next)\s+week", normalised)
    if match:
        weekday = recurrence.WEEKDAYS.get(match.group(1))
        if weekday is not None:
            today = datetime.datetime.now().date()
            week_start = today - datetime.timedelta(days=today.weekday())
            start = week_start + datetime.timedelta(days=weekday)
            if match.group(2) == "next":
                start += datetime.timedelta(days=7)
            return Schedule(key, start, recurrence.FORTNIGHTLY, 13)

    return None


def _describe(record, source):
    column = record.get("column", "")
    text = record.get("value", "")
    if column in _TYPE_MAP and text:
        schedule = _phrase_to_schedule(text, column)
        if schedule is not None:
            yield schedule


@final
class Source(BaseSource):
    TITLE = "City of Kwinana"
    DESCRIPTION = "Source for City of Kwinana waste collection."
    URL = "https://www.kwinana.wa.gov.au"
    COUNTRY = "au"

    TEST_CASES = {
        "Kwinana Town Centre": {"address": "1 Chisham Avenue KWINANA TOWN CENTRE"},
        "Wellard": {"address": "25 Breccia Parade WELLARD"},
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '25 Breccia Parade WELLARD')."
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG, address="address")
    parse = IntraMapsPanelParser()
    preprocessor = RecurrenceExpander(_describe)

    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
