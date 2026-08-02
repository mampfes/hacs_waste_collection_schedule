from datetime import date, datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.ArcGis import geocoded_params
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Jacksonville has no FeatureServer to query: the ArcGIS World GeocodeServer
# resolves the address to a point and a bespoke custhelp.com XML endpoint is
# keyed by that point. Geocoding is request-building, so it composes as the
# params of the shared HTTP retriever (geocoded_params) rather than a
# source-local retrieve. There is no recurring cadence to project either: each
# XML section reports one explicit next date, so _describe() yields a
# single-occurrence Schedule per section and a plain ICSTransformer types them.

SITE_URL = "https://myjax.custhelp.com/app/hauler"
API_URL = (
    "https://myjax.custhelp.com/cgi-bin/myjax.cfg/php/custom/src/callgisservice.php"
)

DATE_FORMAT = "%m/%d/%Y"
TIMEOUT = 30

NS = {"tns": "https://cityofjacksonville.custhelp.com/"}

# (XML section, date tag, waste-type key)
COLLECTIONS = (
    ("GARBAGEWASTE", "PICKUPDATE", "Garbage"),
    ("YARDWASTE", "PICKUPDATE", "Yard Waste"),
    ("RECYWASTE", "PICKUPDATE", "Recycling"),
    ("BULKWASTE", "PICKUPDATE", "Bulk Waste"),
    ("TIREWASTE", "TIRE_PICKUP_DATE", "Tires"),
    ("APPLIANCEWASTE", "PICKUPDATE", "Appliances"),
)

_TYPE_MAP = {
    "Garbage": GENERAL_WASTE,
    "Yard Waste": GARDEN_WASTE,
    "Recycling": RECYCLABLES,
    "Bulk Waste": BULKY_WASTE,
    "Tires": BULKY_WASTE,
    "Appliances": BULKY_WASTE,
}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


def _describe(root, source):
    """Yield the one dated collection each XML section reports."""
    error = root.findtext("ERROR")
    if error:
        raise SourceArgumentNotFound("address", source.params["address"], error)

    for section, date_tag, waste_type in COLLECTIONS:
        collection_date = _parse_date(
            root.findtext(f"tns:{section}/tns:{date_tag}", namespaces=NS)
        )
        if collection_date is not None:
            yield Schedule(waste_type, collection_date, count=1)


@final
class Source(BaseSource):
    TITLE = "Jacksonville, FL"
    DESCRIPTION = "Source for Jacksonville, FL waste collection."
    URL = SITE_URL
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@biggiebytes"]

    TEST_CASES: ClassVar[dict] = {
        "EverBank Stadium": {"address": "1 EverBank Stadium Dr, Jacksonville, FL"},
        "Mandarin": {"address": "11743 Heather Grove Ln, Jacksonville, FL"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Use the same address you would enter on the MyJax hauler lookup page.",
    }

    retrieve = retrievers.HttpGetRetriever(
        url=API_URL,
        params=geocoded_params(lon_param="lng", extra={"intersection": "n"}),
        headers={"Referer": SITE_URL, "User-Agent": "Mozilla/5.0"},
        timeout=TIMEOUT,
    )
    parse = parsers.XmlParser()
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())
