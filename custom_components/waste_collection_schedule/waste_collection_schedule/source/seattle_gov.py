from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address, text_field
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.service.SeattleUtilities import SeattleUtilitiesRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Seattle Public Utilities"
    DESCRIPTION = "Source for Seattle Public Utilities waste collection."
    URL = "https://myutilities.seattle.gov"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "City Hall": {"street_address": "600 4th Ave"},
        "Ballard Builders": {"street_address": "7022 12th Ave NW"},
        "Carmona Court": {"street_address": "1127 17th Ave E"},
        "2111 E John St": {
            "street_address": "2111 E John St",
            "prem_code": "DRMGcnGxUEg+gu8pN8vesQ==",
        },
    }

    PARAMS = (
        street_address("street_address"),
        text_field("prem_code", "Premise code", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street address of the property, e.g. '600 4th Ave'. "
            "If the address lookup picks the wrong property, enter its premise "
            "code (the `premCode` the calendar lookup page at "
            "https://myutilities.seattle.gov/eportal/#/accountlookup/calendar "
            "receives for your address) as well."
        ),
    }

    retrieve = SeattleUtilitiesRetriever()

    parse = parsers.JsonParser("services")

    preprocess = ExplodeList("dates", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="description",
        parse_date=date_parsers.for_format("%m/%d/%Y"),
        type_value_map={
            "Garbage": wt.GENERAL_WASTE,
            "Recycle": wt.RECYCLABLES,
            "Food/Yard Waste": wt.ORGANIC,
        },
    )
