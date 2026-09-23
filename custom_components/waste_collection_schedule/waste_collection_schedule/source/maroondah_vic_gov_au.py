from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    TYPE_VALUE_MAP,
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Maroondah City Council"
    DESCRIPTION = "Source for Maroondah City Council. Finds both green waste and general recycling dates."
    URL = "https://www.maroondah.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Monday - Area A": {"address": "1 Abbey Court, RINGWOOD 3134"},
        "Monday - Area B": {"address": "1 Angelica Crescent, CROYDON HILLS 3136"},
        "Tuesday - Area B": {"address": "6 Como Close, CROYDON 3136"},
        "Wednesday - Area A": {"address": "113 Dublin Road, RINGWOOD EAST 3135"},
        "Wednesday - Area B": {"address": "282 Maroondah Highway, RINGWOOD 3134"},
        "Thursday - Area A": {"address": "4 Albury Court, CROYDON NORTH 3136"},
        "Thursday - Area B": {"address": "54 Lincoln Road, CROYDON 3136"},
        "Friday - Area A": {"address": "6 Lionel Crescent, CROYDON 3136"},
        "Friday - Area B": {"address": "61 Timms Avenue, KILSYTH 3137"},
    }

    PARAMS = (street_address(field="address"),)

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    retrieve = OpenCitiesRetriever(
        domain="https://www.maroondah.vic.gov.au",
        warm_up_url="https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule",
        headers={
            "Accept": "text/plain, */*; q=0.01",
            "Referer": "https://www.maroondah.vic.gov.au/Residents-property/Waste-rubbish/Waste-collection-schedule",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            **TYPE_VALUE_MAP,
        },
    )
