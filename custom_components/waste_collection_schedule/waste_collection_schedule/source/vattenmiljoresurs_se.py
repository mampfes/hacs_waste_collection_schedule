from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street_address
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.SitevisionGarbageCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Vatten och Miljöresurs"
    DESCRIPTION = (
        "Source for Vatten och Miljöresurs waste collection in Jämtland, Sweden."
    )
    URL = "https://www.vattenmiljoresurs.se"
    COUNTRY = "se"
    TEST_CASES: ClassVar[dict] = {
        "Bräcke - Hantverksgatan 25": {
            "municipality": "bracke",
            "street_address": "Hantverksgatan 25",
        },
        "Berg - Balviken 550, Svenstavik": {
            "municipality": "berg",
            "street_address": "Balviken 550",
        },
        "Härjedalen - Algatan 3, Sveg": {
            "municipality": "harjedalen",
            "street_address": "Algatan 3",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "Find your address on the provider website for your municipality and enter it exactly as shown (street name and number)."
    }
    REGIONS = (
        Region(
            title="Bräcke",
            params={"municipality": "bracke"},
            url="https://www.vattenmiljoresurs.se/bracke/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
            country="se",
        ),
        Region(
            title="Berg",
            params={"municipality": "berg"},
            url="https://www.vattenmiljoresurs.se/berg/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
            country="se",
        ),
        Region(
            title="Härjedalen",
            params={"municipality": "harjedalen"},
            url="https://www.vattenmiljoresurs.se/harjedalen/avfall-och-atervinning/avfallshamtning/nar-kommer-sopbilen",
            country="se",
        ),
    )
    PARAMS = (
        municipality(),
        street_address("street_address"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Hushållsavfall": wt.GENERAL_WASTE,
        },
    )
