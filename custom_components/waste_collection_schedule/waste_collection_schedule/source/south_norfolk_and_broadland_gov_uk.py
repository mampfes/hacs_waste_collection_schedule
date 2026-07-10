import calendar
import json
import re
from datetime import date
from html import unescape
from time import strptime
from typing import List
from urllib.parse import quote
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup as soup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Broadland District Council"
DESCRIPTION = "Source for southnorfolkandbroadland.gov.uk services for South Norfolk and Broadland, UK"
URL = "https://area.southnorfolkandbroadland.gov.uk/"
EXTRA_INFO = [
    {
        "title": "South Norfolk Council",
        "url": "https://southnorfolkandbroadland.gov.uk/",
    },
]
TEST_CASES = {
    "Broadland residential address - UPRN payload": {
        "address_payload": {
            "Uprn": "010014355477",
            "Address": "29 Mallard Way, Sprowston, Norwich, Norfolk, NR7 8DN",
            "X": "626227.00000",
            "Y": "312136.00000",
            "Ward": "Sprowston East",
            "Parish": "Sprowston",
            "Village": "Sprowston",
            "Street": "Mallard Way",
            "Authority": "2610",
        }
    },
    "Broadland residential address - postcode": {
        "postcode": "NR7 8DN",
        "address": "29 Mallard Way, Sprowston, Norfolk, NR7 8DN",
    },
    "South Norfolk residential address - UPRN payload": {
        "address_payload": {
            "Uprn": "002630130840",
            "Address": "1 Brindle Drive, Mulbarton, Norfolk, NR14 8BX",
            "X": "619142.00000",
            "Y": "300585.00000",
            "Ward": "Mulbarton And Stoke Holy Cross",
            "Parish": "Mulbarton",
            "Village": "Mulbarton",
            "Street": "Brindle Drive",
            "Authority": "2630",
        }
    },
    "South Norfolk residential address - postcode": {
        "postcode": "NR14 8BX",
        "address": "1 Brindle Drive, Mulbarton, Norfolk, NR14 8BX",
    },
    "Broadland business address (Tesco) - UPRN payload": {
        "address_payload": {
            "Uprn": "100091575309",
            "Address": "Tesco Stores Ltd, Blue Boar Lane, Sprowston, Norwich, Norfolk, NR7 8AB",
            "X": "625657.00000",
            "Y": "312146.00000",
            "Ward": "Sprowston East",
            "Parish": "Sprowston",
            "Village": "Sprowston",
            "Street": "Blue Boar Lane",
            "Authority": "2610",
        }
    },
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden (if applicable)": Icons.GARDEN,
    "Garden": Icons.GARDEN,
    "Food": Icons.BIO_KITCHEN,
}

# South Norfolk dedicated calendar endpoint (present on My Area page for SNC addresses only)
_SNC_CALENDAR_HOST = "collections-southnorfolk.azurewebsites.net"
_SNC_SOAP_URL = f"https://{_SNC_CALENDAR_HOST}/WSCollExternal.asmx"
_SNC_SOAP_NS = "http://webaspx-collections.azurewebsites.net/"
_SNC_SOAP_ACTION = (
    '"http://webaspx-collections.azurewebsites.net/getRoundCalendarForUPRN"'
)

# SVG <title> prefixes -> waste-type display names used by this source
_SNC_BIN_TYPE_PREFIXES = {
    "Ref": "Rubbish",
    "Rec": "Recycling",
    "Foo": "Food",
    "Grn": "Garden",
    "Gar": "Garden",
}


matcher = re.compile(r"^([A-Z][a-z]+) (\d{1,2}) ([A-Z][a-z]+) (\d{4})$")


def parse_date(date_str: str) -> date:
    match = matcher.match(date_str)
    if match is None:
        raise ValueError(f"Unable to parse date {date_str}")

    return date(
        int(match.group(4)),
        strptime(match.group(3)[:3], "%b").tm_mon,
        int(match.group(2)),
    )


def comparable(data: str) -> str:
    return data.replace(",", "").replace(" ", "").lower()


def _parse_snc_svg_title(title_text: str) -> List[str]:
    """Extract waste-type names from the SVG <title> inside a calendar cell.

    Each line of the title looks like 'Rec date based on Round Name' or
    'Foo affected by start date of container'.  We match by prefix.
    """
    bin_types: List[str] = []
    for line in title_text.strip().split("\n"):
        line = line.strip()
        for prefix, name in _SNC_BIN_TYPE_PREFIXES.items():
            if line.startswith(prefix) and name not in bin_types:
                bin_types.append(name)
                break
    return bin_types


def _fetch_snc_soap_calendar(uprn: str) -> List[Collection]:
    """Fetch and parse the South Norfolk SOAP calendar for a given UPRN.

    The SOAP endpoint returns an HTML calendar where each collection day that
    applies to this property contains an SVG pie-chart icon.  The SVG's
    <title> element identifies which bin type(s) are collected on that day.

    This bypasses the My Area summary page which incorrectly reports the next
    upcoming date for each bin type (making Rubbish and Recycling appear on the
    same day when they actually alternate fortnightly).
    """
    soap_body = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body>"
        f'<getRoundCalendarForUPRN xmlns="{_SNC_SOAP_NS}">'
        "<council>SNO</council>"
        "<webServicePassword></webServicePassword>"
        "<username></username>"
        "<usernamePassword></usernamePassword>"
        f"<UPRN>{uprn}</UPRN>"
        "<from>Chtml</from>"
        "</getRoundCalendarForUPRN>"
        "</soap:Body>"
        "</soap:Envelope>"
    )

    r = requests.post(
        _SNC_SOAP_URL,
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": _SNC_SOAP_ACTION,
        },
        data=soap_body.encode("utf-8"),
    )
    r.raise_for_status()

    root = ET.fromstring(r.text)
    ns = f"{{{_SNC_SOAP_NS}}}"
    result_el = root.find(f".//{ns}getRoundCalendarForUPRNResult")
    if result_el is None or not result_el.text:
        return []

    html = unescape(result_el.text)
    page = soup(html, "html.parser")

    results: List[Collection] = []
    seen: set = set()

    for table in page.find_all("table", id=lambda x: x and x.startswith("CalTab")):
        th = table.find("th", class_="thMidHC")
        if not th:
            continue
        month_str = th.get_text(strip=True)
        try:
            month_name_str, year_str = month_str.split(" ")
            year = int(year_str)
            month_num = list(calendar.month_name).index(month_name_str)
        except (ValueError, IndexError):
            continue

        first_weekday, days_in_month = calendar.monthrange(year, month_num)
        for row_idx, row in enumerate(
            table.find_all("tr")[2:]
        ):  # skip month-header and day-name rows
            for col_idx, cell in enumerate(
                row.find_all("td")[1:]
            ):  # skip leading empty td
                # Calculate the actual day-of-month from grid position.
                # The calendar is a Mon-Sun grid; first_weekday (Mon=0) tells us
                # how many leading padding cells appear before day 1.
                day = row_idx * 7 + col_idx - first_weekday + 1
                if day < 1 or day > days_in_month:
                    continue  # padding cell before or after month

                svg = cell.find("svg")
                if not svg:
                    continue  # no collection for this property on this day

                title_el = svg.find("title")
                if not title_el:
                    continue

                bin_types = _parse_snc_svg_title(title_el.get_text())
                try:
                    d = date(year, month_num, day)
                except ValueError:
                    continue

                for bt in bin_types:
                    key = (d, bt)
                    if key not in seen:
                        seen.add(key)
                        results.append(Collection(d, bt, icon=ICON_MAP.get(bt)))

    return results


class Source:
    _address_payload: dict | None

    def __init__(
        self,
        address_payload: dict | None = None,
        postcode: str | None = None,
        address: str | None = None,
    ):
        self._address_payload = address_payload
        self._postcode = comparable(postcode) if postcode else None
        self._address = address if address else None

    def fetch(self) -> List[Collection]:
        if self._address_payload:
            return self.__fetch_by_payload()
        return self.__fetch_by_postcode_and_address()

    def __fetch_by_postcode_and_address(self) -> List[Collection]:
        if not self._postcode or not self._address:
            errors = []
            if self._postcode:
                errors.append("address")
            elif self._address:
                errors.append("postcode")
            else:
                errors = ["address_payload", "postcode", "address"]
            raise SourceArgumentExceptionMultiple(
                errors,
                "Either (address_payload) or (postcode and address) must be provided",
            )

        session = requests.Session()
        r = session.get(URL + "FindAddress")
        r.raise_for_status()
        page = soup(r.text, "html.parser")

        args = {
            "Postcode": self._postcode,
            "__RequestVerificationToken": page.find(
                "input", {"name": "__RequestVerificationToken"}
            )["value"],
        }
        r = session.post(URL + "FindAddress", data=args)
        r.raise_for_status()
        page = soup(r.text, "html.parser")
        addresses = page.find("select", {"id": "UprnAddress"}).find_all("option")

        if not addresses:
            raise SourceArgumentNotFound("postcode", self._postcode)

        args["__RequestVerificationToken"] = page.find(
            "input", {"name": "__RequestVerificationToken"}
        )["value"]

        found = False
        compare_address = self._address.replace(",", "").replace(" ", "").lower()

        for address in addresses:
            address_text = comparable(address.text)

            if (
                address_text == compare_address
                or address_text == compare_address.replace(self._postcode, "")
            ):
                args["UprnAddress"] = address["value"]
                found = True
                break

        if not found:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, [address.text for address in addresses]
            )

        r = session.post(URL + "FindAddress/Submit", data=args)
        r.raise_for_status()
        return self.__get_data(r)

    def __fetch_by_payload(self) -> List[Collection]:
        r = requests.get(
            URL,
            headers={
                "Cookie": f"MyArea.Data={quote(json.dumps(self._address_payload))}"
            },
        )
        r.raise_for_status()
        return self.__get_data(r)

    def __get_data(self, r: requests.Response) -> List[Collection]:
        page = soup(r.text, "html.parser")
        bins_card = page.find("h3", string="Bins").parent

        # South Norfolk addresses show a "View your bin calendar" link pointing to
        # collections-southnorfolk.azurewebsites.net.  The My Area summary page
        # only shows the next upcoming date per bin type which causes Rubbish and
        # Recycling to appear on the same day for addresses on an alternating
        # fortnightly schedule.  When the link is present we use the dedicated
        # SOAP calendar endpoint which returns the correct per-type dates.
        snc_link = bins_card.find("a", href=lambda h: h and _SNC_CALENDAR_HOST in h)
        if snc_link:
            m = re.search(r"UPRN=(\d+)", snc_link["href"])
            if m:
                return _fetch_snc_soap_calendar(m.group(1))

        # Broadland (and any SNC address without the calendar link): use My Area data.
        bin_categories = bins_card.find_all("div", {"class": "card-text"})
        return [
            Collection(
                parse_date(tuple(bin_category.children)[3].strip()),
                tuple(bin_category.children)[1].text.strip(),
                icon=ICON_MAP.get(tuple(bin_category.children)[1].text.strip()),
            )
            for bin_category in bin_categories
        ]
