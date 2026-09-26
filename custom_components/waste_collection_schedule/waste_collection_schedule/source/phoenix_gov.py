from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import WeekdayRecurrence
from waste_collection_schedule.service.ArcGis import (
    ArcGisMultiFeatureParser,
    ArcGisMultiFeatureRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# City of Phoenix Public Works "GarbagePickUp" MapServer.
# Layer 2 = PW_GARBAGE (trash collection zones), layer 1 = PW_RECYCLE
# (recycling collection zones). Both layers expose a single "DOC"
# (day of collection) field, e.g. "FRIDAY".
_MAPSERVER = "https://maps.phoenix.gov/pub/rest/services/Public/GarbagePickUp/MapServer"


@final
class Source(BaseSource):
    TITLE = "Phoenix, AZ"
    DESCRIPTION = "Source for City of Phoenix, AZ trash and recycling collection."
    URL = "https://www.phoenix.gov/publicworks/garbage/trashschedule/find-your-day-of-collection"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "4750 S 48th St, Phoenix, AZ 85040": {
            "address": "4750 S 48th St, Phoenix, AZ 85040"
        },
        "With suite number": {"address": "4750 S 48th St SUITE 121, Phoenix, AZ 85040"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the full street address including city and state (e.g. "
            "'4750 S 48th St, Phoenix, AZ 85040')."
        ),
    }

    # Not every address is eligible for city recycling service (some
    # multi-family or commercial buildings), so a layer that does not contain
    # the point simply contributes nothing.
    retrieve = ArcGisMultiFeatureRetriever(
        [
            ("Trash", f"{_MAPSERVER}/2", "DOC"),
            ("Recycling", f"{_MAPSERVER}/1", "DOC"),
        ]
    )
    parse = ArcGisMultiFeatureParser(first_per_layer=True)
    preprocess = WeekdayRecurrence(
        day=lambda record: record[1].get("DOC"),
        keys=lambda record: record[0],
    )
    transform = ICSTransformer(
        type_value_map={"Trash": wt.GENERAL_WASTE, "Recycling": wt.RECYCLABLES}
    )
