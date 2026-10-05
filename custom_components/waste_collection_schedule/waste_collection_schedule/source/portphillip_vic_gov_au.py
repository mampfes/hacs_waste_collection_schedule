from typing import ClassVar, final

from waste_collection_schedule import recurrence
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

INTRAMAPS_CONFIG = MapsClientConfig(
    base_url="https://copp.spatial.t1cloud.com",
    instance="spatial/IntraMaps",
    config_id="15f21a6e-3939-4b70-b531-21309d0624de",
    project="3bf491de-10d3-42f0-be95-716bd4263526",
    lite_config_id="b0b09c2e-b120-4a07-84f3-fd8c1dbecb6e",
    module_id="e948c801-51b4-452a-87b5-2627e0e3e01a",
    selection_layer_filter="a6b80f49-ccbc-4b7c-8560-c1c15ac6164c",
)

# The "Bin Collection" column is a weekday name, e.g. "Wednesday". The council
# collects general waste, recycling and FOGO together, once a week, on that day.
_BINS = {
    "General Waste": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "FOGO": wt.ORGANIC,
}
_WEEKS = 26


def _describe(record, source):
    if record.get("column") != "Bin Collection":
        return
    weekday = recurrence.weekday(record.get("value", "").strip())
    if weekday is None:
        return
    start = recurrence.next_weekday(weekday)
    for key in _BINS:
        yield Schedule(key, start, recurrence.WEEKLY, _WEEKS)


@final
class Source(BaseSource):
    TITLE = "City of Port Phillip"
    DESCRIPTION = "Source for City of Port Phillip waste collection."
    URL = "https://www.portphillip.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "9 Spray Street Elwood": {"address": "9 Spray Street Elwood"},
        "99A Bridport Street Albert Park": {
            "address": "99A Bridport Street Albert Park"
        },
        "1 Beach Street Port Melbourne": {"address": "1 Beach Street Port Melbourne"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "99 Nowhere Street Elwood"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb (e.g. '9 Spray Street "
            "Elwood'). Search at https://www.portphillip.vic.gov.au/"
            "council-services/waste-recycling-and-rubbish/bins-and-collection-services"
        ),
    }

    retrieve = IntraMapsRetriever(INTRAMAPS_CONFIG)
    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_BINS)
