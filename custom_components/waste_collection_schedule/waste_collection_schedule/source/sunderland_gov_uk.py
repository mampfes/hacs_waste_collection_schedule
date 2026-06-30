import base64
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Sunderland City Council"
DESCRIPTION = "Source for sunderland.gov.uk services for Sunderland City Council, UK."
URL = "https://www.sunderland.gov.uk/"
PAGE_URL = "https://www.sunderland.gov.uk/bindays"
SUBMIT_URL = "https://www.sunderland.gov.uk/apiserver/formsservice/http/processsubmission"
FORM_PREFIX = "BINCOLLECTIONCHECKERNEWV3"
HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

TEST_CASES = {
    "Test_001": {"postcode": "SR4 7PU", "address": "191 Cleveland Road"},
    "Test_002": {"postcode": "SR3 2DW", "address": "43 Hill Street"},
    "Test_003": {"postcode": "SR4 8RJ", "address": "17 Sutherland Drive"},
}

ICON_MAP = {
    "Household Green Bin": Icons.GENERAL_WASTE,
    "Blue Recycling Bin": Icons.RECYCLING,
    "Garden Waste": Icons.GARDEN,
}


class Source:
    def __init__(self, postcode: str, address: str):
        self._postcode = str(postcode).strip()
        self._address = str(address).strip()

    def _get_hidden_fields(self, soup: BeautifulSoup) -> dict:
        """Extract all hidden input fields from the form."""
        fields = {}
        for tag in soup.find_all("input", type="hidden"):
            name = tag.get("name", "")
            if name.startswith(FORM_PREFIX):
                fields[name] = tag.get("value", "")
        return fields

    def _get_submit_url(self, soup: BeautifulSoup) -> str:
        """Extract the processsubmission URL from the form action."""
        form = soup.find("form", id=f"{FORM_PREFIX}_FORM")
        if form and form.get("action"):
            return form["action"]
        raise ValueError("Could not find form action URL in page")

    def fetch(self):
        s = requests.Session()
        s.headers.update(HEADERS)

        # Step 1: GET the bin checker page to obtain session IDs and nonce
        r = s.get(PAGE_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        fields = self._get_hidden_fields(soup)
        submit_url = self._get_submit_url(soup)

        # Step 2: POST postcode to trigger address lookup
        payload = dict(fields)
        payload.update({
            f"{FORM_PREFIX}_PAGENAME": "ADDRESSSEARCH",
            f"{FORM_PREFIX}_PAGEINSTANCE": "0",
            f"{FORM_PREFIX}_ADDRESSSEARCH_SCCPOSTCODE": self._postcode,
            f"{FORM_PREFIX}_FORMACTION_NEXT": f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODETRIGGER",
            f"{FORM_PREFIX}_ADDRESSSEARCH_SCCLISTOFADDRESSES": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODE": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_UPRN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_RESIDUALBIN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_TRADEBIN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_RECYCLEBIN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_GARDENBIN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_NEXTBIN": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_PDFURL": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_LAT": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_LNG": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_ADDRESSTEXT": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_DATARETURNED": "",
            f"{FORM_PREFIX}_ADDRESSSEARCH_DATARETURNED2": "",
        })

        r = s.post(submit_url, data=payload, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Step 3: Extract address list from VARIABLES hidden field (base64 encoded JSON)
        fields = self._get_hidden_fields(soup)
        submit_url = self._get_submit_url(soup)

        variables_b64 = fields.get(f"{FORM_PREFIX}_VARIABLES", "")
        if not variables_b64:
            raise ValueError("No address data returned for postcode. Check postcode is correct.")

        variables = json.loads(base64.b64decode(variables_b64).decode())

        # postcodefoundoptionset is a list of [uprn, display_address, ""] entries
        # First entry is always ["", "Please select", ""]
        address_options = variables.get("postcodefoundoptionset", {}).get("value", [])
        full_details = variables.get("postcodefoundfulldetails", {}).get("value", [])

        # Match the user's address string (case-insensitive, comma/whitespace normalised)
        def normalise(s: str) -> str:
            return re.sub(r"[\s,]+", " ", s).strip().lower()

        uprn = None
        matched_address = None
        normalised_input = normalise(self._address)
        for option in address_options[1:]:  # skip "Please select"
            if normalised_input in normalise(option[1]):
                uprn = option[0]
                matched_address = option[1]
                break

        if uprn is None:
            available = [o[1] for o in address_options[1:]]
            raise ValueError(
                f"Address '{self._address}' not found in results for postcode '{self._postcode}'. "
                f"Available addresses: {available}"
            )

        # Step 4: POST with selected UPRN to retrieve collection dates
        payload = dict(fields)
        payload.update({
            f"{FORM_PREFIX}_PAGENAME": "ADDRESSSEARCH",
            f"{FORM_PREFIX}_PAGEINSTANCE": "1",
            f"{FORM_PREFIX}_ADDRESSSEARCH_SCCPOSTCODE": self._postcode,
            f"{FORM_PREFIX}_FORMACTION_NEXT": f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODETRIGGER",
            f"{FORM_PREFIX}_ADDRESSSEARCH_SCCLISTOFADDRESSES": uprn,
            f"{FORM_PREFIX}_ADDRESSSEARCH_POSTCODE": self._postcode,
            f"{FORM_PREFIX}_ADDRESSSEARCH_UPRN": uprn,
            f"{FORM_PREFIX}_ADDRESSSEARCH_ADDRESSTEXT": matched_address,
        })

        r = s.post(submit_url, data=payload, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Step 5: Parse collection dates from results page
        # Dates appear in <p class="myaccount-block__date--bin--waste"> as "Fri Jun 19 2026"
        entries = []
        for bin_type, icon in ICON_MAP.items():
            # Find the title element for this bin type
            title_el = soup.find(
                "p",
                string=re.compile(re.escape(bin_type), re.IGNORECASE),
            )
            if title_el is None:
                continue

            # The date is in a sibling <p> with class containing "myaccount-block__date"
            container = title_el.parent
            date_el = container.find("p", class_=re.compile(r"myaccount-block__date"))
            if date_el is None:
                continue

            date_str = date_el.get_text(strip=True)
            try:
                # Format: "Fri Jun 19 2026"
                date = datetime.strptime(date_str, "%a %b %d %Y").date()
                entries.append(Collection(date=date, t=bin_type, icon=icon))
            except ValueError:
                continue

        return entries

