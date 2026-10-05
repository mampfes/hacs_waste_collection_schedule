from typing import ClassVar, final

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    location_id,
    service_id,
    text_field,
)
from waste_collection_schedule.service.ReCollect import (
    TYPE_VALUE_MAP,
    ReCollectEventsParser,
    events_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "ReCollect (JSON API)"
    DESCRIPTION = "Source for municipalities on the ReCollect (Routeware) platform, via its JSON events API."
    URL = "https://recollect.net"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@muditguptacode"]

    # The vocabulary the recorded cassettes produce.
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Halton Region, ON - 1151 Bronte Rd, Oakville": {
            "place_id": "CD149A08-1F87-11E2-A81F-CD0EC465FF45",
            "service_id": "224",
        },
        "Stirling Council, UK (EU host)": {
            "place_id": "D6ADFBAE-D4AF-11F0-9DA3-EE0251E5C8E1",
            "service_id": "waste",
            "locale": "en-GB",
        },
    }

    REGIONS: ClassVar[list] = [
        regions.region(
            "Halton Region, ON",
            country="ca",
            place_id="CD149A08-1F87-11E2-A81F-CD0EC465FF45",
            service_id="224",
        ),
        regions.region(
            "Stirling Council",
            country="uk",
            place_id="D6ADFBAE-D4AF-11F0-9DA3-EE0251E5C8E1",
            service_id="waste",
            locale="en-GB",
        ),
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Look up your address in your municipality's ReCollect widget and "
            "click 'Get a calendar' to show the calendar link, e.g. "
            "https://recollect.a.ssl.fastly.net/api/places/<place_id>/services/"
            "<service_id>/events.en.ics. Enter the two IDs from that link. "
            "Use this source when that ICS link fails in the ICS source."
        ),
    }

    PARAMS = (
        location_id(field="place_id"),
        service_id(),
        text_field(
            "locale",
            label="Language of the waste type names (e.g. en, fr, en-GB)",
            default="en",
        ),
    )

    retrieve = events_retriever()
    parse = ReCollectEventsParser()
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
