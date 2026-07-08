from datetime import date, datetime
from xml.etree import ElementTree

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisError, geocode

TITLE = "Jacksonville, FL"
DESCRIPTION = "Source for Jacksonville, FL waste collection."
URL = "https://myjax.custhelp.com/app/hauler"
COUNTRY = "us"
SOURCE_CODEOWNERS = ["@biggiebytes"]

TEST_CASES = {
    "EverBank Stadium": {"address": "1 EverBank Stadium Dr, Jacksonville, FL"},
    "Mandarin": {"address": "11743 Heather Grove Ln, Jacksonville, FL"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including city and state (e.g. '11743 Heather Grove Ln, Jacksonville, FL')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Use the same address you would enter on the MyJax hauler lookup page.",
}

API_URL = (
    "https://myjax.custhelp.com/cgi-bin/myjax.cfg/php/custom/src/callgisservice.php"
)

DATE_FORMAT = "%m/%d/%Y"
TIMEOUT = 30

NS = {"tns": "https://cityofjacksonville.custhelp.com/"}

COLLECTIONS = (
    ("GARBAGEWASTE", "PICKUPDATE", "Garbage", Icons.GENERAL_WASTE),
    ("YARDWASTE", "PICKUPDATE", "Yard Waste", Icons.GARDEN),
    ("RECYWASTE", "PICKUPDATE", "Recycling", Icons.RECYCLING),
    ("BULKWASTE", "PICKUPDATE", "Bulk Waste", Icons.BULKY),
    ("TIREWASTE", "TIRE_PICKUP_DATE", "Tires", Icons.BULKY),
    ("APPLIANCEWASTE", "PICKUPDATE", "Appliances", Icons.BULKY),
)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        try:
            location = geocode(self._address)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        response = requests.get(
            API_URL,
            params={
                "lng": location["x"],
                "lat": location["y"],
                "intersection": "n",
            },
            headers={
                "Referer": URL,
                "User-Agent": "Mozilla/5.0",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        try:
            root = ElementTree.fromstring(response.text.strip())
        except ElementTree.ParseError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        error = root.findtext("ERROR")
        if error:
            raise SourceArgumentNotFound("address", self._address, error)

        entries = []

        for section, date_tag, waste_type, icon in COLLECTIONS:
            date_value = root.findtext(f"tns:{section}/tns:{date_tag}", namespaces=NS)
            collection_date = _parse_date(date_value)
            if collection_date is None:
                continue

            entries.append(Collection(date=collection_date, t=waste_type, icon=icon))

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries
