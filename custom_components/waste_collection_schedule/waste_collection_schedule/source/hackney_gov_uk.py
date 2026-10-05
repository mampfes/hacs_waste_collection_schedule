from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.service.AlloyWastePages import AlloyWastePagesRetriever
from waste_collection_schedule.transformers import JsonTransformer

API = "https://waste-api-hackney-live.ieg4.net/f806d91c-e133-43a6-ba9a-c0ae4f4cccf6"

# Hackney names a container after its kind and size: "Recycling Sack",
# "Food Caddy (Small)", "GW_Wheeled Bin 140l", "Wheeled Bin (180ltr)".
_KEYWORDS = (
    ("recycling", "recycling"),
    ("food", "food"),
    ("garden", "garden"),
    ("gw_", "garden"),
    ("180ltr", "refuse"),
    ("240ltr", "refuse"),
    ("wheeled bin", "refuse"),
)


def _kind(label: str) -> str:
    """The first keyword the container name holds, as the legacy source matched."""
    lowered = label.lower()
    for keyword, kind in _KEYWORDS:
        if keyword in lowered:
            return kind
    return label


@final
class Source(BaseSource):
    TITLE = "London Borough of Hackney"
    DESCRIPTION = "Source for London Borough of Hackney Council waste collection."
    URL = "https://www.hackney.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Middleton Road": {"uprn": "100021058914", "postcode": "E8 4LL"},
        "Elrington Road": {"uprn": "100021039326", "postcode": "E8 3BJ"},
        "King Edwards Road": {"uprn": "100021051283", "postcode": "E9 7SL"},
    }

    PARAMS = (uprn(), postcode())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and enter it together with the postcode of the property."
        ),
    }

    retrieve = AlloyWastePagesRetriever(
        API, origin="https://hackney-waste-pages.azurewebsites.net"
    )

    parse = parsers.JsonParser()

    preprocess = ExplodeList("dates", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="name",
        clean=_kind,
        type_value_map={
            "recycling": wt.RECYCLABLES,
            "food": wt.FOOD_WASTE,
            "garden": wt.GARDEN_WASTE,
            "refuse": wt.GENERAL_WASTE,
        },
    )
