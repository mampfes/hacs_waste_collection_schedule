from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, uprn
from waste_collection_schedule.regions import region
from waste_collection_schedule.service import RoundLookup


@final
class Source(BaseSource):
    TITLE = "Malvern Hills District Council"
    DESCRIPTION = "Source for Malvern Hills District Council."
    URL = "https://www.malvernhills.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region(
            "Malvern Hills",
            url="https://www.malvernhills.gov.uk/",
            council="Malvern Hills",
        ),
        region("Wychavon", url="https://www.wychavon.gov.uk/", council="Wychavon"),
        region(
            "Worcester City",
            url="https://www.worcester.gov.uk/",
            council="Worcester City",
        ),
    )

    TEST_CASES: ClassVar[dict] = {
        "1Malvern Hill: s00120597618": {
            "uprn": 100120597618,
            "council": "Malvern Hills",
        },
        "Malvern Hills: 100121268004": {
            "uprn": "100121268004",
            "council": "Malvern Hills",
        },
        "Worcester City: 100120656169": {
            "uprn": 100120656169,
            "council": "Worcester City",
        },
        "Wychavon: 10095592085": {"uprn": 10095592085, "council": "Wychavon"},
    }

    PARAMS = (uprn(), dropdown("council", list(RoundLookup.API_URLS), label="Council"))

    WASTE_TYPES: ClassVar[list] = RoundLookup.WASTE_TYPES

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering your address details."
        ),
    }

    retrieve = RoundLookup.retriever()
    parse = RoundLookup.PARSE
    preprocess = staticmethod(RoundLookup.rows)
    transform = RoundLookup.TRANSFORM
