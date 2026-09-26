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
    TITLE = "Palmerston North City Council"
    DESCRIPTION = (
        "Source for Palmerston North City Council rubbish and recycling collections."
    )
    URL = "https://www.pncc.govt.nz/Services/Rubbish-and-recycling/Palmy-Collections/Rubbish-and-recycling-days"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "8 Swansea Street, Hokowhitu": {"address": "8 Swansea Street Palmerston North"},
        "1 Broadway Avenue": {"address": "1 Broadway Avenue Palmerston North"},
    }

    PARAMS = (street_address(field="address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your street address as it appears in the search on the "
        "Palmerston North City Council 'Rubbish and recycling days' page, for "
        "example '8 Swansea Street Palmerston North'."
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GLASS]

    retrieve = OpenCitiesRetriever(
        domain="https://www.pncc.govt.nz",
    )
    parse = OpenCitiesParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        description_key="note",
        type_value_map={"Glass Crate": wt.GLASS, "Wheelie Bin": wt.RECYCLABLES},
    )
