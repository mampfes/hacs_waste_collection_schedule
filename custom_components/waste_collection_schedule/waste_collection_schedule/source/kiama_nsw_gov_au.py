from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Kiama City Council"
    DESCRIPTION = "Source script for kiama.nsw.gov.au"
    URL = "https://kiama.nsw.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "TestName1": {"geolocationid": "3e54d9b4-e0b8-41cf-8518-d48c1cc5407b"},
        "TestName2": {"geolocationid": "0d96e409-7a81-4ccb-a0d8-d8435e066182"},
    }

    PARAMS = (location_id(field="geolocationid"),)

    HOWTO: ClassVar[dict] = {
        "en": "Go to "
        "<https://www.kiama.nsw.gov.au/Services/Waste-and-recycling/Find-my-bin-collection-dates>\n"
        "Open the developer tools (F12), Go to the Network tab\n"
        "Put in your address, and click Search.\n"
        "\n"
        "Look for a network call to the wasteservices endpoint, it will have "
        "geolocationid=<GUID>\n"
        "This GUID is what you need, it is unique to your service address."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.kiama.nsw.gov.au",
        address=None,
        geolocation_id="geolocationid",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "Urban garbage": wt.GENERAL_WASTE,
            "Urban recycling": wt.RECYCLABLES,
            "Urban food & garden organics": wt.ORGANIC,
        },
    )
