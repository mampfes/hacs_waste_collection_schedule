import logging
from datetime import date, datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (  # type: ignore[attr-defined]
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Preston City Council"
DESCRIPTION = "Source for preston.gov.uk services for Preston City Council, UK."
URL = "https://preston.gov.uk"
COUNTRY = "uk"
SRV_URL = (
    "https://selfservice.preston.gov.uk/service/Forms/FindMyNearest.aspx?Service=bins"
)

TEST_CASES = {
    "Test_001": {"street": "town hall, lancaster road"},
    "Test_002": {"street": "PR1 2RL", "uprn": "10002220003"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street / Postcode",
        "uprn": "UPRN (optional)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Your street name or postcode (required). Used to search for your address.",
        "uprn": "Your Unique Property Reference Number (optional). When provided alongside street/postcode, it picks the exact matching property from the search results. Leave blank if you are unsure.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your postcode or street name in the 'Street / Postcode' field. If your postcode returns multiple properties, find your UPRN at https://www.findmyaddress.co.uk/ and enter it in the optional 'UPRN' field to select the exact property."
}

ICON_MAP = {
    "Food waste:": Icons.BIO_KITCHEN,
    "Commercial -  general waste:": Icons.COMMERCIAL,
    "Commercial -  cardboard and paper:": Icons.PAPER,
    "Commercial - plastic cans and glass:": Icons.PLASTIC_PACKAGING,
    "Commercial -  food waste:": Icons.BIO_KITCHEN,
    "Black/grey bin (general waste):": Icons.GENERAL_WASTE,
    "Yellow lidded recycling container (glass/cans/plastics):": Icons.PLASTIC_PACKAGING,
    "Red lidded recycling container (paper/card):": Icons.PAPER,
    "Brown bin (garden waste):": Icons.BIO_KITCHEN,
}

HEADER_MAP = {
    "Food waste:": "Food Waste",
    "Commercial -  general waste:": "General Waste (Commercial)",
    "Commercial -  cardboard and paper:": "Cardboard (Commercial)",
    "Commercial - plastic cans and glass:": "Plastic (Commercial)",
    "Commercial -  food waste:": "Food Waste (Commercial)",
    "Black/grey bin (general waste):": "General Waste (Black/Grey bin)",
    "Yellow lidded recycling container (glass/cans/plastics):": "Glass/Cans/Plastics (Yellow bin)",
    "Red lidded recycling container (paper/card):": "Cardboard/Paper (Red bin)",
    "Brown bin (garden waste):": "Garden/Green Waste (Brown bin)",
}

_LOGGER = logging.getLogger(__name__)


def _extract_hidden_inputs(soup: BeautifulSoup) -> dict:
    """Extract all hidden input fields from a BeautifulSoup page."""
    params = {}
    for inp in soup.find_all("input", {"type": "hidden"}):
        name = inp.get("name")
        value = inp.get("value", "")
        if name:
            params[name] = value
    return params


class Source:
    def __init__(self, street="", uprn=""):
        self._street = street
        self._uprn = str(uprn)

    def fetch(self) -> list:
        if not self._street:
            raise SourceArgumentNotFound(
                argument="street",
                value=self._street,
            )

        session = requests.Session(impersonate="chrome")

        # Step 1: GET the initial page to obtain session cookies and hidden ASP.NET fields
        r0 = session.get(SRV_URL)
        r0.raise_for_status()
        soup0 = BeautifulSoup(r0.text, features="html.parser")

        # Step 2: POST the search request with address/postcode
        params1 = _extract_hidden_inputs(soup0)
        params1["__EVENTTARGET"] = "ctl00$MainContent$btnSearch"
        params1["__EVENTARGUMENT"] = ""
        params1["ctl00$MainContent$hdnService"] = "bins"
        params1["ctl00$MainContent$txtAddress"] = self._street
        params1["ctl00$MainContent$hdnUPRN"] = self._uprn

        r1 = session.post(SRV_URL, data=params1)
        r1.raise_for_status()
        soup1 = BeautifulSoup(r1.text, features="html.parser")

        # Check whether the search already returned collection data
        cnt = soup1.select_one("span#MainContent_lblMoreCollectionDates")
        if cnt and cnt.find_all("div", {"id": "container"}):
            return self._parse(cnt)

        # Step 3: Select from the address dropdown (triggered by ddlSearchResults change)
        select_el = soup1.find("select", {"name": "ctl00$MainContent$ddlSearchResults"})
        if not select_el:
            raise SourceArgumentNotFound(
                argument="street",
                value=self._street,
            )

        options = [
            opt
            for opt in select_el.find_all("option")
            if opt.get("value", "").startswith("170|")
            or opt.get("value", "").count("|") >= 4
        ]

        if not options:
            # Build suggestions from all non-placeholder options
            all_opts = [
                opt.text.strip()
                for opt in select_el.find_all("option")
                if opt.get("value", "") not in ("Make a selection from the list", "")
            ]
            raise SourceArgumentNotFoundWithSuggestions(
                argument="street",
                value=self._street,
                suggestions=all_opts,
            )

        # Pick the best matching option
        selected_option = options[0]
        if self._uprn:
            for opt in options:
                if self._uprn in (opt.get("value", "") + opt.text):
                    selected_option = opt
                    break

        if len(options) > 1 and not self._uprn:
            _LOGGER.warning(
                "Multiple addresses found for %r, using first: %s",
                self._street,
                selected_option.text.strip(),
            )

        selected_value = selected_option.get("value", "")

        params2 = _extract_hidden_inputs(soup1)
        params2["__EVENTTARGET"] = "ctl00$MainContent$ddlSearchResults"
        params2["__EVENTARGUMENT"] = ""
        params2["ctl00$MainContent$hdnService"] = "bins"
        params2["ctl00$MainContent$txtAddress"] = self._street
        params2["ctl00$MainContent$ddlSearchResults"] = selected_value

        r2 = session.post(SRV_URL, data=params2)
        r2.raise_for_status()
        soup2 = BeautifulSoup(r2.text, features="html.parser")

        cnt = soup2.select_one("span#MainContent_lblMoreCollectionDates")
        if not cnt or not cnt.find_all("div", {"id": "container"}):
            raise SourceArgumentNotFound(
                argument="street",
                value=self._street,
            )

        return self._parse(cnt)

    @staticmethod
    def _date(date_string: str) -> date | None:
        try:
            return datetime.strptime(date_string, "%A %d/%m/%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse(cnt) -> list:
        entries = []

        for blk in cnt.find_all("div", {"id": "container"}):
            header_sel = blk.select_one("ul > b")
            if not header_sel:
                continue
            header_txt = header_sel.text.strip()

            hdr = HEADER_MAP.get(header_txt) or header_txt.rstrip(":")
            ico = ICON_MAP.get(header_txt)

            for itm in blk.select("ul > li"):
                date_span = itm.select_one("span")
                if not date_span:
                    continue
                date_obj = Source._date(date_span.text.strip())
                if date_obj is None:
                    continue
                entries.append(Collection(t=hdr, date=date_obj, icon=ico))

        return entries
