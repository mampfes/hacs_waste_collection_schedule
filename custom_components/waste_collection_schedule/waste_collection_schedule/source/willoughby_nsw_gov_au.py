from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

BASE_URL = "https://www.willoughby.nsw.gov.au"


@final
class Source(BaseSource):
    TITLE = "Willoughby City Council"
    DESCRIPTION = "Source for Willoughby City Council waste collection."
    URL = "https://www.willoughby.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "18 Crabbes Avenue, North Willoughby": {
            "address": "18 Crabbes Avenue, North Willoughby, NSW 2068",
        },
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Visit the Willoughby City Council waste service dates page, search "
        "for your address, and use the address text as shown by the lookup.",
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    retrieve = OpenCitiesRetriever(
        domain=BASE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": (
                f"{BASE_URL}/Residents/Waste-and-recycling/"
                "Household-bin-services/Waste-and-street-sweeping-services"
            ),
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Weekly red-lidded garbage bin collection": wt.GENERAL_WASTE,
            "Weekly yellow-lidded recycling bin collection": wt.RECYCLABLES,
            "Weekly green-lidded vegetation bin collection": wt.GARDEN_WASTE,
            "Street sweeping service": wt.OTHER,
        },
    )
