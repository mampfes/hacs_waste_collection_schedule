"""City of Airdrie (AB) curbside collection calendar.

The collection schedules page (``index.cfm?serviceID=1880``) loads every
community's dated garbage, recycling and organics collections from one JSON
feed and filters it in the browser by the community chosen in its dropdown.
The source reads the same feed and keeps the rows of the configured community.
"""

from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.preprocessors import (
    Compose,
    RequireRecords,
    RowFilter,
)
from waste_collection_schedule.transformers import JsonTransformer

API_URL = "https://www.airdrie.ca/functions/WasteRecycling/getEvents"

# The names offered by the page's community dropdown. The feed spells them in
# upper case and without the apostrophe ("KINGS HEIGHTS"), see _community_key.
COMMUNITIES = [
    "Airdrie Meadows",
    "Bayside",
    "Baysprings",
    "Bayview",
    "Big Springs",
    "Canals",
    "Chinook Gate",
    "Cobblestone Creek",
    "Coopers Crossing",
    "Downtown",
    "Edgewater",
    "Fairways",
    "Hillcrest",
    "Jensen",
    "Key Ranch",
    "King's Heights",
    "Lanark",
    "Luxstone",
    "Meadowbrook",
    "Midtown",
    "Morningside",
    "Old Town",
    "Prairie Springs",
    "Ravenswood",
    "Reunion",
    "Ridgegate",
    "Sagewood",
    "Sawgrass Park",
    "Silver Creek",
    "South Point",
    "South Windsong",
    "Southwinds",
    "Stonegate",
    "Summerhill",
    "Sunridge",
    "The Village",
    "Thorburn",
    "Vantage Rise",
    "Waterstone",
    "Wildflower",
    "Williamstown",
    "Willowbrook",
    "Windsong",
    "Woodside",
]


class _Props(TypedDict):
    communities: str


class _Event(TypedDict):
    title: str
    start: str
    extendedProps: _Props


def _community_key(name: str) -> str:
    return " ".join(name.replace("'", "").replace("’", "").upper().split())


def _in_community(event: _Event, source: "BaseSource | None") -> bool:
    if source is None:
        return False
    wanted = _community_key(source.params["community"])
    return wanted in {
        _community_key(name)
        for name in event["extendedProps"]["communities"].split(",")
    }


@final
class Source(BaseSource):
    TITLE = "Airdrie (AB)"
    DESCRIPTION = "City of Airdrie waste collection"
    URL = "https://www.airdrie.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]

    TEST_CASES: ClassVar[dict] = {
        "Coopers Crossing": {"community": "Coopers Crossing"},
        "Morningside": {"community": "Morningside"},
        "Bayside": {"community": "Bayside"},
        "King's Heights": {"community": "King's Heights"},
    }

    PARAMS = (dropdown("community", COMMUNITIES, label="Community"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your community as named on the City of Airdrie "
            "[collection schedules page](https://www.airdrie.ca/index.cfm?serviceID=1880). "
            "The [Waste and recycling community map](https://www.airdrie.ca/getLink.cfm?ID=13995) "
            "shows which community an address belongs to."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(url=API_URL)
    parse = parsers.JsonParser(shape=list[_Event])
    preprocess = Compose(
        RowFilter(_in_community),
        RequireRecords(
            argument="community",
            suggestions=lambda source: COMMUNITIES,
        ),
    )
    transform = JsonTransformer(
        # "2026-04-06 07:00:00.0000000": the collection day, carts out by 7 a.m.
        date_key=lambda event: event["start"][:10],
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Garbage collection": wt.GENERAL_WASTE,
            "Black garbage cart collection": wt.GENERAL_WASTE,
            "Recycling collection": wt.RECYCLABLES,
            "Blue recycling cart collection": wt.RECYCLABLES,
            "Organics collection": wt.ORGANIC,
            "Green organics cart collection": wt.ORGANIC,
        },
    )
