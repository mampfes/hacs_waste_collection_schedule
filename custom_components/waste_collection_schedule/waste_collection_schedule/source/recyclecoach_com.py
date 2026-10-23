from typing import Any, ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street, text_field
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.RecycleCoach import (
    RecycleCoachParser,
    RecycleCoachRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

# Labels that announce a day without collection rather than a collection.
_NO_COLLECTION = (
    "Holiday",
    "Stat Holiday - No Collection",
    "No Collection Day",
)

_TYPE_MAP: dict[str, Any] = {
    **dict.fromkeys(_NO_COLLECTION, None),
    **dict.fromkeys(
        (
            "Garbage Collection",
            "Garbage Service",
            "Waste Collection",
            "Trash Collection",
            "Red Landfill",
            "Blue Zone Garbage",
            "Grey Household Waste Cart",
            "Garbage (Residual Waste)",
            "Waste",
        ),
        wt.GENERAL_WASTE,
    ),
    "Trash/Bulk Items": [wt.GENERAL_WASTE, wt.BULKY_WASTE],
    **dict.fromkeys(
        (
            "Green Bin Collection",
            "Green Bin",
            "Green Bin Organics",
            "Green Can",
            "Organics",
            "Green Organic Waste Cart",
            "Organics Collection",
        ),
        wt.ORGANIC,
    ),
    **dict.fromkeys(
        (
            "Recycling Collection",
            "Recycle Collection",
            "Blue Box",
            "Blue Box Recycling",
            "Blue Box Collection",
            "Blue Box (Container) Recycling",
            "Container Recycling",
            "Commingled Recycling",
            "Blue Recycling Cart",
            "Yellow Bin",
            "Yellow Bin Container Recycling",
        ),
        wt.RECYCLABLES,
    ),
    **dict.fromkeys(
        (
            "Paper Recycling",
            "Blue Bin Paper Recycling",
            "Green Box (Fibre) Recycling",
        ),
        wt.PAPER,
    ),
    **dict.fromkeys(
        (
            "Yard Waste Collection",
            "Yard Waste Collection Week",
            "Leaf and Yard Waste",
            "Leaf & Yard Waste Collection",
            "Leaf",
            "Brush",
        ),
        wt.GARDEN_WASTE,
    ),
    **dict.fromkeys(
        ("Large Item Collection", "Brush and Bulky Collection"), wt.BULKY_WASTE
    ),
    "Curbside Battery Collection": wt.HAZARDOUS,
    "Newmarket Electronics Recycling Event": wt.ELECTRONICS,
    **dict.fromkeys(
        (
            "Treecycle",
            "Christmas Tree",
            "Christmas Tree Collection",
            "Christmas Tree Drop Off",
            "Christmas Tree Drop-off Depots Open",
            "Saturday Drop-Off Site",
            "Curbside Giveaway",
            "Curbside Giveaway Days",
            "Double-Up Days",
            "3 Container Exemption Pick-up",
            "3 Bags of Waste",
            "Seasonal Roads Collection",
            "Event",
        ),
        wt.OTHER,
    ),
}

# Label of the records that are an event of the municipality, not a collection.
_EVENT = "Event"


def _label(record: dict) -> str:
    """The title of a collection; events other than the mapped ones share one label."""
    title = record["title"]
    if record["kind"] == "EVENT" and title.strip().lower() not in _KNOWN:
        return _EVENT
    return title


def _description(record: dict) -> str | None:
    """The title of an event, which its shared label does not say."""
    return record["title"] if _label(record) == _EVENT else None


_KNOWN = {label.strip().lower() for label in _TYPE_MAP}


@final
class Source(BaseSource):
    TITLE = "Recycle Coach"
    DESCRIPTION = "Source loader for recyclecoach.com"
    URL = "https://recyclecoach.com"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.HAZARDOUS,
        wt.ELECTRONICS,
        wt.OTHER,
    ]

    REGIONS = (
        region(
            "Albuquerque, New Mexico, USA",
            url="https://recyclecoach.com/cities/usa-nm-city-of-albuquerque/",
            city="Albuquerque",
            state="New Mexico",
        ),
        region(
            "Tucson, Arizona, USA",
            url="https://recyclecoach.com/cities/usa-az-city-of-tucson/",
            city="Tucson",
            state="Arizona",
        ),
        region(
            "Olympia, Washington, USA",
            url="https://recyclecoach.com/cities/usa-wa-city-of-olympia/",
            city="Olympia",
            state="Washington",
        ),
        region(
            "Tacoma, Washington, USA",
            url="https://recyclecoach.com/cities/usa-wa-city-of-tacoma/",
            city="Tacoma",
            state="Washington",
        ),
        region(
            "Newark, Delaware, USA",
            url="https://recyclecoach.com/cities/usa-de-city-of-newark/",
            city="Newark",
            state="Delaware",
        ),
        region(
            "Louisville, Kentucky, USA",
            url="https://recyclecoach.com/cities/usa-ky-city-of-louisville/",
            city="Louisville",
            state="Kentucky",
        ),
        region(
            "Frederick County, Maryland, USA",
            url="https://www.frederickcountymd.gov/3447/Curbside-Collection-Schedule",
            city="Frederick County",
            state="Maryland",
        ),
        region(
            "Palm Beach County, Florida, USA",
            url="https://www.swa.org/518/Pickup-Schedule",
            city="Palm Beach County",
            state="Florida",
        ),
        region(
            "London (ON)",
            url="https://london.ca/",
            country="ca",
            city="London",
            state="Ontario",
        ),
        region(
            "Aurora (ON)",
            url="https://www.aurora.ca/",
            country="ca",
            city="Aurora",
            state="Ontario",
        ),
        region(
            "Vaughan (ON)",
            url="https://www.vaughan.ca/",
            country="ca",
            city="Vaughan",
            state="Ontario",
        ),
        region(
            "Richmond Hill (ON)",
            url="https://www.richmondhill.ca/",
            country="ca",
            city="Richmond Hill",
            state="Ontario",
        ),
        region(
            "Kawartha Lakes (ON)",
            url="https://www.kawarthalakes.ca/",
            country="ca",
            city="Kawartha Lakes",
            state="Ontario",
        ),
        region(
            "Norfolk County (ON)",
            url="https://www.norfolkcounty.ca/",
            country="ca",
            project_id="3107",
            district_id="OLYMP",
        ),
        region(
            "Oak Bay (BC)",
            url="https://www.oakbay.ca/",
            country="ca",
            project_id="3187",
            district_id="OAK",
        ),
        region(
            "Prince George (BC)",
            url="https://www.princegeorge.ca/",
            country="ca",
            project_id="523",
            district_id="PrinceGeorge",
        ),
        region(
            "City of Hamilton (ON)",
            url="https://www.hamilton.ca/",
            country="ca",
            project_id="520",
            district_id="HAM",
        ),
        region(
            "Chatham-Kent (ON)",
            url="https://www.chatham-kent.ca/",
            country="ca",
            city="Chatham-Kent",
            state="Ontario",
        ),
        region(
            "Delta (BC)",
            url="https://www.delta.ca/",
            country="ca",
            city="Delta",
            state="British Columbia",
        ),
        region(
            "Burnaby (BC)",
            url="https://www.burnaby.ca/",
            country="ca",
            city="Burnaby",
            state="British Columbia",
        ),
        region(
            "Orillia (ON)",
            url="https://www.orillia.ca/",
            country="ca",
            city="Orillia",
            state="Ontario",
        ),
        region(
            "Medicine Hat (AB)",
            url="https://www.medicinehat.ca/",
            country="ca",
            project_id="500",
            district_id="MEDHAT",
            zone_id="zone-z196",
        ),
        region(
            "Township of Langley (BC)",
            url="https://www.tol.ca/",
            country="ca",
            project_id="521",
            district_id="LANGL",
        ),
        region(
            "East Gwillimbury (ON)",
            url="https://www.eastgwillimbury.ca/",
            country="ca",
            project_id="586",
            district_id="EASTG",
        ),
        region(
            "Brantford (ON)",
            url="https://www.brantford.ca/",
            country="ca",
            project_id="3195",
            district_id="BRAN",
        ),
        region(
            "Kelowna (BC)",
            url="https://www.rdco.com/",
            country="ca",
            project_id="502",
            district_id="Kelowna",
        ),
        region(
            "West Kelowna (BC)",
            url="https://www.rdco.com/",
            country="ca",
            project_id="502",
            district_id="WestKelowna",
        ),
        region(
            "Plainville (CT)",
            url="https://www.plainvillect.com/",
            country="us",
            project_id="3066",
            district_id="PLA",
        ),
        region(
            "LaSalle (ON)",
            url="https://www.lasalle.ca/",
            country="ca",
            project_id="583",
            district_id="LAS",
        ),
        region(
            "Lakeshore (ON)",
            url="https://www.lakeshore.ca/",
            country="ca",
            project_id="583",
            district_id="LAK",
        ),
        region(
            "Glenorchy City Council (TAS)",
            url="https://www.gcc.tas.gov.au/",
            country="au",
            project_id="657",
            district_id="GLENORCHY",
        ),
        region(
            "Byron Shire Council (NSW)",
            url="https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules",
            country="au",
            project_id="592",
            district_id="BYSC",
        ),
        region(
            "Toronto (ON) - Circular Materials",
            url="https://www.toronto.ca/",
            country="ca",
            project_id="CIRCMATONT",
            district_id="TORONTO",
        ),
        region(
            "Mississauga (ON)",
            url="https://www.mississauga.ca/",
            country="ca",
            project_id="3179",
            district_id="MISS",
        ),
        region(
            "Brampton (ON)",
            url="https://www.brampton.ca/",
            country="ca",
            project_id="3179",
            district_id="BRAMP",
        ),
        region(
            "Caledon (ON)",
            url="https://www.caledon.ca/",
            country="ca",
            project_id="3179",
            district_id="CALED",
        ),
        region(
            "Carleton Place (ON)",
            url="https://carletonplace.ca/",
            country="ca",
            project_id="3149",
            district_id="CARLETON",
        ),
        region(
            "Burlington (ON)",
            url="https://www.burlington.ca/",
            country="ca",
            project_id="3169",
            district_id="BURL",
        ),
        region(
            "Oakville (ON)",
            url="https://www.oakville.ca/",
            country="ca",
            project_id="3169",
            district_id="OAKV",
        ),
        region(
            "Milton (ON)",
            url="https://www.milton.ca/",
            country="ca",
            project_id="3169",
            district_id="MILT",
        ),
        region(
            "Halton Hills (ON)",
            url="https://www.haltonhills.ca/",
            country="ca",
            project_id="3169",
            district_id="HALT",
        ),
        region(
            "Guelph (ON)",
            url="https://guelph.ca/",
            country="ca",
            project_id="3194",
            district_id="GUEL",
        ),
        region(
            "New Rochelle (NY)",
            url="https://www.newrochelleny.gov/791/Collection-Dates",
            country="us",
            project_id="3015",
            district_id="NEWRO",
        ),
        region(
            "Peoria (IL)",
            url="https://www.peoriagov.org/533/Yes-Peoria-Picks-Up",
            country="us",
            project_id="PEORIA",
            district_id="PEORIA",
        ),
        region(
            "Bloomington (IL)",
            url="https://www.bloomingtonil.gov/",
            country="us",
            project_id="621",
            district_id="BLO",
        ),
        region(
            "Newmarket (ON)",
            url="https://www.newmarket.ca/",
            country="ca",
            project_id="530",
            district_id="NEW",
        ),
    )

    TEST_CASES: ClassVar[dict] = {
        "Default": {
            "street": "2242 grinstead drive",
            "city": "louisville",
            "state": "KY",
        },
        "Problematic City Lookup": {
            "street": "2202 E Florence Dr",
            "city": "Tucson",
            "state": "AZ",
            "district_id": "TUC",
            "project_id": "532",
        },
        "olympia": {
            "street": "1003 Lybarger St NE",
            "city": "Olympia",
            "state": "Washington",
        },
        "newark": {"street": "24 Townsend Rd", "city": "Newark", "state": "Delaware"},
        "albuquerque": {
            "street": "1505 Silver Ave SE",
            "city": "Albuquerque",
            "state": "New Mexico",
        },
        "london ontario": {
            "street": "1065 Sunningdale Rd E",
            "city": "London",
            "state": "Ontario",
        },
        "london ontario with districtID": {
            "street": "1065 Sunningdale Rd E",
            "city": "London",
            "state": "Ontario",
            "project_id": "528",
            "district_id": "CityofLondon",
            "zone_id": "zone-z547",
        },
        "aurora ontario": {
            "street": "123 Cranberry Lane",
            "city": "Aurora",
            "state": "Ontario",
        },
        "Vaughan, Ontario, Canada": {
            "street": "Main St",
            "city": "Vaughan",
            "state": "Ontario",
        },
        "67 Baseline Rd Coboconk, ON": {
            "street": "67 Baseline Rd",
            "city": "Coboconk",
            "state": "Ontario",
        },
        "Richmond Hill, Ontario, Canada": {
            "street": "10235 Yonge Street",
            "city": "Richmond Hill",
            "state": "Ontario",
        },
        "Norfolk County, Ontario, Canada (with district_id, project_id & zone_id)": {
            "district_id": "OLYMP",
            "project_id": 3107,
            "zone_id": "zone-z11266-z16205-z16208-z16218",
        },
        "Oak Bay, BC, Canada (with district_id, project_id & zone_id)": {
            "district_id": "OAK",
            "project_id": 3187,
            "zone_id": "zone-z20122",
        },
        "Prince George, BC, Canada (with district_id, project_id & zone_id)": {
            "district_id": "PrinceGeorge",
            "project_id": 523,
            "zone_id": "zone-z483-z1860",
        },
        "City of Hamilton, ON, Canada (with district_id, project_id & zone_id)": {
            "district_id": "HAM",
            "project_id": 520,
            "zone_id": "zone-z1151",
        },
        "Chatham-Kent, ON, Canada (API results have trailing space)": {
            "street": "20 Bloomfield Rd",
            "city": "Chatham-Kent",
            "state": "Ontario",
        },
        "6656 Ladner Trunk Rd, Delta, BC V4K 5C8, Kanada": {
            "street": "6656 Ladner Trunk Rd",
            "city": "Delta",
            "state": "British Columbia",
        },
        "Burnaby, BC, Canada": {
            "street": "215 Gilmore Ave N",
            "city": "Burnaby",
            "state": "British Columbia",
        },
        "City of Medicine Hat, AB, Canada (with district_id, project_id & zone_id)": {
            "district_id": "MEDHAT",
            "project_id": 500,
            "zone_id": "zone-z196",
        },
        "Glenorchy City Council, TAS, Australia": {
            "district_id": "GLENORCHY",
            "project_id": 657,
            "zone_id": "zone-z15322-z16165-z16823",
        },
        "Lakeshore, ON, Canada (with district_id, project_id & zone_id)": {
            "district_id": "LAK",
            "project_id": 583,
            "zone_id": "zone-z9942",
        },
        "New Rochelle, NY, USA (with district_id, project_id & zone_id)": {
            "district_id": "NEWRO",
            "project_id": 3015,
            "zone_id": "zone-z19582-z19705",
        },
        "West Kelowna, BC, Canada (with district_id & project_id)": {
            "street": "2760 Cameron Rd",
            "city": "West Kelowna",
            "state": "British Columbia",
            "district_id": "WestKelowna",
            "project_id": "502",
        },
        "Peoria, IL, USA": {
            "street": "10303 N Churchill Dr",
            "city": "Peoria",
            "state": "Illinois",
        },
        "Bloomington, IL, USA (with district_id, project_id & zone_id)": {
            "district_id": "BLO",
            "project_id": "621",
            "zone_id": "zone-z11025",
        },
        "Byron Shire Council, NSW, Australia": {
            "street": "120 Jonson St, Byron Bay",
            "project_id": "592",
            "district_id": "BYSC",
        },
        "Carleton Place, ON, Canada": {
            "street": "175 Bridge St",
            "city": "Carleton Place",
            "state": "Ontario",
        },
        "Frederick County, MD, USA (with district_id, project_id & zone_id)": {
            "district_id": "FRE",
            "project_id": "527",
            "zone_id": "zone-z652",
        },
        "Palm Beach County, FL, USA (with district_id, project_id & zone_id)": {
            "district_id": "PB",
            "project_id": "633",
            "zone_id": "zone-z21670-z21652-z21659-z21666",
        },
        "Newmarket, ON, Canada (with district_id, project_id & zone_id)": {
            "district_id": "NEW",
            "project_id": "530",
            "zone_id": "zone-z12563",
        },
    }

    PARAMS = (
        street(optional=True),
        city(optional=True),
        text_field("state", "State / Province", optional=True),
        text_field(
            "project_id",
            "Project ID",
            optional=True,
            coerce=lambda value: str(value).strip(),
        ),
        text_field(
            "district_id",
            "District ID",
            optional=True,
            coerce=lambda value: str(value).strip(),
        ),
        text_field("zone_id", "Zone ID", optional=True),
    )

    retrieve = RecycleCoachRetriever()
    parse = RecycleCoachParser()
    transform = JsonTransformer(
        date_key="date",
        type_key=_label,
        description_key=_description,
        type_value_map=_TYPE_MAP,
        carry_raw_label=True,
    )
