from typing import ClassVar, final

from waste_collection_schedule import regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.service.WasteInfo import (
    COUNCILS,
    TYPE_VALUE_MAP,
    WasteInfoEventsParser,
    WasteInfoRetriever,
    council_api,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Impact Apps"
    DESCRIPTION = (
        "Source for councils using Impact Apps (waste-info.com.au) for waste "
        "collection."
    )
    URL = "https://impactapps.com.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.ORGANIC,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Random Redland Bay": {
            "service": "redland",
            "suburb": "Redland Bay",
            "street_name": "Boundary Street",
            "street_number": "1",
        },
        "Teneriffe Green Beacon": {
            "service": "https://brisbane.waste-info.com.au",
            "suburb": "Teneriffe",
            "street_name": "Helen St",
            "street_number": "26",
        },
        "Test Penrith Address": {
            "service": "Penrith City Council",
            "property_id": 71794,
        },
        "Random Penrith Address": {
            "service": "Penrith City Council",
            "suburb": "Emu Plains",
            "street_name": "Beach Street",
            "street_number": "3",
        },
        "Blue Mountains": {
            "service": "Blue Mountains City Council",
            "suburb": "Katoomba",
            "street_name": "Katoomba Street",
            "street_number": "110",
        },
        "Bayside Council, NSW": {
            "service": "Bayside Council",
            "suburb": "Eastlakes",
            "street_name": "Universal Street",
            "street_number": "5",
        },
        "Wollongong": {"service": "wollongong", "property_id": 21444},
        "Ballarat": {"service": "ballarat", "property_id": 34195},
        "Bega Valley": {"service": "bega", "property_id": 43106},
        "Burwood": {"service": "burwood", "property_id": 7821},
        "Campbelltown": {"service": "campbelltown", "property_id": 255933},
        "Canada Bay": {"service": "canada-bay", "property_id": 10475},
        "Cowra": {"service": "cowra", "property_id": 3585},
        "Cumberland": {"service": "cumberland", "property_id": 260324},
        "Forbes": {"service": "forbes", "property_id": 1694},
        "Gwydir": {"service": "gwydir", "property_id": 645},
        "Lithgow": {
            "service": "lithgow",
            "suburb": "Clarence",
            "street_name": "Chifley Road",
            "street_number": "590",
        },
        "Livingstone": {"service": "livingstone", "property_id": 26730},
        "Moira": {"service": "moira", "property_id": 24492},
        "Moree Plains": {"service": "moree", "property_id": 4570},
        "Port Stephens": {"service": "port-stephens", "property_id": 5149},
        "PMHC": {"service": "pmhc", "property_id": 19297},
        "QPRC": {"service": "qprc", "property_id": 116719},
        "South Burnett": {"service": "south-burnett", "property_id": 30012},
        "Wellington": {"service": "wellington", "property_id": 1456},
        "Baw-Baw": {"service": "baw-baw", "property_id": 12894},
        "Snowy Valleys": {"service": "snowy-valleys", "property_id": 6787},
        "Gympie": {
            "service": "gympie",
            "suburb": "Cooloola Cove",
            "street_name": "Investigator Av",
            "street_number": "11",
        },
        "Benalla": {
            "service": "benalla",
            "suburb": "Benalla",
            "street_name": "Arundel Street",
            "street_number": "110",
        },
        "Coffs Coast": {
            "service": "coffs-coast",
            "suburb": "North Dorrigo",
            "street_name": "Tyringham Road",
            "street_number": "666",
        },
        "Ku-ring-gai": {
            "service": "ku-ring-gai",
            "suburb": "St Ives",
            "street_name": "Kitchener Street",
            "street_number": "99/2-8",
        },
        "Horsham Rural City": {
            "service": "hrcc",
            "suburb": "Mckenzie Creek",
            "street_name": "Henty Highway",
            "street_number": "3999",
        },
        "Murrindindi Shire Council": {
            "service": "murrindindi",
            "suburb": "Yea",
            "street_name": "The Parade",
            "street_number": "44",
        },
        "Clarence Valley Council": {
            "service": "clarence",
            "suburb": "Yamba",
            "street_name": "Wattle Drive",
            "street_number": "24",
        },
    }

    PARAMS = (
        text_field("service", "Service"),
        text_field("property_id", "Property ID", optional=True),
        text_field("suburb", "Suburb", optional=True),
        street("street_name", optional=True),
        house_number("street_number", optional=True),
    )

    REGIONS = tuple(
        regions.region(council.name, url=council.website, service=council.name)
        for council in COUNCILS
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Service: the council's name as listed, its waste-info.com.au API URL "
            "(e.g. 'https://brisbane.waste-info.com.au'), or the first part of "
            "that host name (e.g. 'brisbane'). Then either the suburb, street name "
            "and street number, or the property ID, which the council's calendar "
            "page requests as '<property ID>.json' (browser developer tools, "
            "Network tab)."
        ),
    }

    retrieve = WasteInfoRetriever(
        lambda service, **_: council_api(service), property_id="property_id"
    )
    parse = WasteInfoEventsParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=TYPE_VALUE_MAP,
        description_key="name",
    )
