from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://geoapi.dorsetcouncil.gov.uk/v1/Services"
_SERVICES = ("refuseday", "recyclingday", "gardenwasteday", "foodwasteday")


@final
class Source(BaseSource):
    TITLE = "Dorset Council"
    DESCRIPTION = (
        "The local authority for the non-metropolitan county of Dorset in England"
    )
    URL = "https://www.dorsetcouncil.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100040606062},
        "Test_002": {"uprn": 100040606087},
        "Test_003": {"uprn": "100040606071"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and entering your address details."
        ),
    }

    # One call per service; a service the property does not have (e.g. garden
    # waste) answers with an empty `values` list.
    retrieve = retrievers.FanOutRetriever(
        targets=lambda source, _: [
            f"{_API}/{service}/{source.params['uprn']}" for service in _SERVICES
        ],
    )

    parse = parsers.EachResponse(parsers.JsonParser("values"))

    transform = JsonTransformer(
        date_key="dateNextVisit",
        type_key="type",
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
        },
    )
