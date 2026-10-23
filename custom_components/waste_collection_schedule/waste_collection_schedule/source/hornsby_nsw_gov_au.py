from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesProjection,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Hornsby Shire Council"
    DESCRIPTION = "Source for Hornsby Shire Council."
    URL = "https://hornsby.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "1 Cherrybrook Road, West Pennant Hills, 2125": {
            "address": "1 Cherrybrook Road, West Pennant Hills, 2125"
        },
        "10 Albion Street, Pennant Hills, 2120": {
            "address": "10 Albion Street, Pennant Hills, 2120"
        },
        # An apartment block: the garbage round runs on two weekdays and the
        # recycling round is given as a weekday only.
        "5 Park Avenue, Waitara, 2077": {"address": "5 Park Avenue, Waitara, 2077"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Search for your address on the Hornsby Shire Council website "
        "(Property > Waste and recycling) and enter it as it appears in the "
        "autocomplete result, e.g. `1 Cherrybrook Road, West Pennant Hills, 2125`."
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]

    # Hornsby sits behind Akamai, which fingerprints the TLS handshake as well
    # as the headers; the default curl_cffi session passes.
    retrieve = OpenCitiesRetriever(
        domain="https://www.hornsby.nsw.gov.au",
        headers={
            "Accept": "application/json, */*",
            "Referer": "https://www.hornsby.nsw.gov.au/",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    # The widget gives the next date per bin (a bare weekday for garbage and,
    # for apartments, recycling; a plain dd/mm/yyyy for bulky waste); the note
    # says how often it repeats.
    parse = OpenCitiesParser(approximate_dates=True, weekday_dates=True)
    preprocess = OpenCitiesProjection(weeks=52)
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Green Waste": wt.GARDEN_WASTE,
            "Bulky Waste": wt.BULKY_WASTE,
            "Bulky Waste for apartments": wt.BULKY_WASTE,
        },
    )
