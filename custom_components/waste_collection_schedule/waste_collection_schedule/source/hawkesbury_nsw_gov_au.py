import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    postcode,
    street,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import (
    Compose,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://data.hawkesbury.nsw.gov.au/api/records/1.0/search/"

# The council's address register spells street types out in full.
_STREET_TYPES = {
    "Av": "Avenue",
    "Cct": "Circuit",
    "Cr": "Crescent",
    "Ct": "Court",
    "Dr": "Drive",
    "Esp": "Esplanade",
    "Gr": "Grove",
    "Hts": "Heights",
    "Hwy": "Highway",
    "Pde": "Parade",
    "Pl": "Place",
    "Rd": "Road",
    "St": "Street",
    "Tce": "Terrace",
}
_BINS = ("garbagebin", "recyclebin", "organicbin")
_DAYS_AHEAD = 365


def _gis_address(suburb, street, houseNo, postCode, **_) -> str:
    """The register key: ``<no> <Street Name> <SUBURB> NSW <postcode>``."""
    name = street.lower()
    for short, full in _STREET_TYPES.items():
        name = re.sub(rf"\b{short.lower()}\b", full, name)
    return f"{houseNo} {name.title()} {suburb.upper()} NSW {postCode}"


def _query(suburb, street, houseNo, postCode, **_) -> dict:
    return {
        "sort": "gisaddress",
        "refine.gisaddress": _gis_address(suburb, street, houseNo, postCode),
        "rows": 1,
        "dataset": "bin-collection-days",
        "timezone": "Australia/Sydney",
        "lang": "en",
    }


def _property(response, source) -> list[dict]:
    """The fields of the property's record (a miss is a wrong house number)."""
    records = response["records"]
    if not records:
        raise SourceArgumentNotFound("houseNo", source.params["houseNo"])
    return [records[-1]["fields"]]


def _schedules(fields, source):
    """One recurring series per bin: a base date and a cadence in days."""
    for name in _BINS:
        frequency = int(fields.get(f"{name}_schedule", 0))
        base = fields.get(f"{name}_week1")
        if frequency == 0 or not base:
            continue
        yield Schedule(
            name,
            date_parsers.auto(base),
            datetime.timedelta(days=frequency),
            _DAYS_AHEAD // frequency + 1,
            anchor=True,
        )


@final
class Source(BaseSource):
    TITLE = "The Hawkesbury City Council, Sydney"
    DESCRIPTION = (
        "Source for Hawkesbury City Council, Sydney, Australia waste collection."
    )
    URL = "https://www.hawkesbury.nsw.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "south windsor, 539a George Street": {
            "suburb": "south windsor",
            "street": "George Street",
            "houseNo": 539,
            "postCode": 2756,
        },
        "Windsor, catherine street 7": {
            "suburb": "Windsor",
            "street": "catherine st",
            "houseNo": 7,
            "postCode": 2756,
        },
        "Kurrajong, Bells Line Of Road 1052 ": {
            "suburb": "Kurrajong HILLS",
            "street": "Bells Line Of Road",
            "houseNo": 1052,
            "postCode": 2758,
        },
    }

    PARAMS = (
        city("suburb"),
        street("street"),
        postcode("postCode", "houseNo"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the suburb, street name (abbreviations such as 'St' or "
            "'Rd' are expanded), house number and postcode of your property."
        ),
    }

    retrieve = retrievers.Request(API_URL, params=_query)
    parse = parsers.JsonParser()
    preprocess = Compose(_property, RecurrenceExpander(_schedules))
    transform = ICSTransformer(
        type_value_map={
            "garbagebin": wt.GENERAL_WASTE,
            "recyclebin": wt.RECYCLABLES,
            "organicbin": wt.ORGANIC,
        }
    )
