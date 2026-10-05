from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.OpenCities import (
    OpenCitiesParser,
    OpenCitiesRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Macedon Ranges Shire Council"
    DESCRIPTION = "Source for Macedon Ranges Shire Council rubbish collection."
    URL = "https://www.mrsc.vic.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Macedon IGA": {"street_address": "20 Victoria Street, Macedon"},
        "ALDI Gisborne": {"street_address": "45 Aitken Street, Gisborne"},
    }

    PARAMS = (street_address(field="street_address"),)

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GLASS,
    ]

    retrieve = OpenCitiesRetriever(
        domain="https://www.mrsc.vic.gov.au",
        address="street_address",
        warm_up_url="https://www.mrsc.vic.gov.au/Live-Work/Bins-Rubbish-Recycling/Bins-and-collection-days/Bin-collection-days",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={
            "FOGO bin": wt.ORGANIC,
            "Recycling bin": wt.RECYCLABLES,
            "Glass-only bin": wt.GLASS,
            "Rubbish/general waste bin": wt.GENERAL_WASTE,
        },
    )
