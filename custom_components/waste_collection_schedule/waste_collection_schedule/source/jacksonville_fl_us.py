from datetime import date, datetime
from typing import ClassVar, final
from xml.etree import ElementTree

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Jacksonville has no FeatureServer to query: the ArcGIS World GeocodeServer
# resolves the address to a point (the one thing the shared ArcGis service
# still contributes here), but the schedule itself comes from a bespoke
# custhelp.com XML endpoint keyed by that point, not an ArcGIS /query. That
# combination -- an external geocode feeding a wholly different, namespaced
# XML API -- is a genuinely irregular flow no configured retriever expresses,
# so retrieve/parse are overridden as methods rather than composed from
# declarative pieces. There is no recurring cadence to project either (each
# section reports one explicit next date), so parse yields (date, key) rows
# directly and a plain ICSTransformer types them.

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


@final
class Source(BaseSource):
    TITLE = "Jacksonville, FL"
    DESCRIPTION = "Source for Jacksonville, FL waste collection."
    URL = "https://myjax.custhelp.com/app/hauler"
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

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address.strip())

    def retrieve(self, source: "Source"):
        address = self.params["address"]
        try:
            location = geocode(address)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", address) from e

        return self.session.get(
            API_URL,
            params={
                "lng": location["x"],
                "lat": location["y"],
                "intersection": "n",
            },
            headers={
                "Referer": self.URL,
                "User-Agent": "Mozilla/5.0",
            },
            timeout=TIMEOUT,
        )

    def parse(self, response, source: "Source | None" = None) -> list[tuple[date, str]]:
        address = self.params["address"]
        try:
            root = ElementTree.fromstring(response.text.strip())
        except ElementTree.ParseError as e:
            raise SourceArgumentNotFound("address", address) from e

        error = root.findtext("ERROR")
        if error:
            raise SourceArgumentNotFound("address", address, error)

        records: list[tuple[date, str]] = []
        for section, date_tag, waste_type in COLLECTIONS:
            date_value = root.findtext(f"tns:{section}/tns:{date_tag}", namespaces=NS)
            collection_date = _parse_date(date_value)
            if collection_date is not None:
                records.append((collection_date, waste_type))
        return records
