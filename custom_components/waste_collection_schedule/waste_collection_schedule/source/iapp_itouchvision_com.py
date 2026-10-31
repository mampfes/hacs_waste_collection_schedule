from typing import ClassVar, final

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, uprn
from waste_collection_schedule.service.ITouchVision import (
    MUNICIPALITIES,
    TYPE_MAP,
    ITouchVisionParser,
    ITouchVisionRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Somerset's published UPRN (30071272) currently answers ``collectionDay: null``.
# Buckinghamshire's published UPRN (100080550517) gets no portal schedule.
# Aylesbury Vale covers that same portal. Hyndburn's host answers 403 to a
# plain client and 200 to the pipeline's Chrome-impersonating session.
_WASTE_TYPES = [
    wt.FOOD_WASTE,
    wt.GARDEN_WASTE,
    wt.GENERAL_WASTE,
    wt.GLASS,
    wt.ORGANIC,
    wt.PAPER,
    wt.RECYCLABLES,
]


@final
class Source(BaseSource):
    TITLE = "iTouchVision Source using the encrypted API"
    DESCRIPTION = "Source for iTouchVision Source using the encrypted API."
    URL = "https://www.itouchvision.com/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = list(_WASTE_TYPES)

    TEST_CASES: ClassVar[dict] = {
        "newport: 10090955364": {"uprn": "10090955364", "municipality": "NEWPORT"},
        "blaenau gwent: 100100457787": {
            "uprn": "100100457787",
            "municipality": "BLAENAU GWENT",
        },
        "Winchester: 10090844134": {
            "uprn": "10090844134",
            "municipality": "WINCHESTER",
        },
        "Aylesbury Vale: 766251559": {
            "uprn": 766251559,
            "municipality": "AYLESBURY VALE",
        },
        "Test Valley": {"uprn": 100060571645, "municipality": "TEST VALLEY"},
        "Hyndburn": {"uprn": 100010439798, "municipality": "HYNDBURN"},
        "Epsom and Ewell: 100061354185": {
            "uprn": "100061354185",
            "municipality": "EPSOM AND EWELL",
        },
    }

    PARAMS = (
        uprn(),
        dropdown("municipality", list(MUNICIPALITIES), label="Municipality"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your council, then enter the property UPRN. Buckinghamshire "
            "and Aylesbury Vale are read from the My Council Services portal. "
            "The former Chiltern source is this one with municipality "
            "BUCKINGHAMSHIRE."
        ),
    }

    REGIONS = tuple(
        regions.region(council["title"], url=council["url"], municipality=name)
        for name, council in MUNICIPALITIES.items()
    )

    retrieve = ITouchVisionRetriever()
    parse = ITouchVisionParser()
    transform = RowTransformer(type_value_map=TYPE_MAP)
