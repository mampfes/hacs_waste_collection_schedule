from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.ReCollect import (
    API_HOSTS,
    TYPE_VALUE_MAP,
    ReCollectEventsParser,
    address_suggest_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# Stirling Council uses Routeware's ReCollect platform (area "StirlingUK" on the
# European host). The address is resolved to a ReCollect place id through the
# area's own address search, then the shared ReCollect events parser reads the
# place's schedule. (recollect_net serves the same council for a user who
# already has the place id.)


@final
class Source(BaseSource):
    TITLE = "Stirling Council"
    DESCRIPTION = "Source for Stirling Council waste collection services."
    URL = "https://www.stirling.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@nagug"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kildean Road 38": {"address": "38 Kildean Road"},
        "Merlo Buchanan Castle Estate": {"address": "Merlo"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Visit https://www.stirling.gov.uk/bins-and-recycling/bin-collection-dates-search/ "
            "and type your address into the search to see the exact wording, then use "
            "the same here. House number and street (e.g. '38 Kildean Road'), property "
            "name (e.g. 'Merlo'), or a single-dwelling postcode work."
        ),
    }

    retrieve = address_suggest_retriever(
        area="StirlingUK", host=API_HOSTS[1], locale="en-GB"
    )
    parse = ReCollectEventsParser(place_id="address")
    transform = ICSTransformer(type_value_map=TYPE_VALUE_MAP)
