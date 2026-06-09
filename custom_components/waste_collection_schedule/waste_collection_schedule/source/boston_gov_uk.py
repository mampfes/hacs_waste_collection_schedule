import base64
import json
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Boston Borough Council"
DESCRIPTION = "Source for www.boston.gov.uk services for Boston Borough Council, UK."
URL = "https://www.boston.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "43 Tarry Hill, Swineshead, PE20 3LW": {
        "postcode": "PE20 3LW",
        "property": "43",
    },
    "The Old Vicarage, Church Close, PE21 6NE": {
        "postcode": "PE21 6NE",
        "property": "10",
    },
}

ICON_MAP = {
    "refusebin": Icons.GENERAL_WASTE,
    "papercardbin": Icons.PAPER,
    "recyclingbin": Icons.RECYCLING,
    "greenbin": Icons.ORGANIC,
    "foodbin": Icons.BIO_KITCHEN,
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "property": "Property name or number",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your property postcode, e.g. PE20 3LW",
        "property": "Your property name or number, e.g. 43",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your postcode and property name or number as they appear on the Boston Borough Council website: https://www.boston.gov.uk/article/27449/Your-Waste-Collections"
}

FORM_URL = "https://www.boston.gov.uk/article/27449/Your-Waste-Collections"
FORM_NAME = "BBCWASTECOLLECTIONSV2"


def _decode_sv(text: str) -> dict:
    """Decode the serialized variables from the GOSS form page."""
    match = re.search(rf"var {FORM_NAME}SerializedVariables = \"([^\"]+)\"", text)
    if not match:
        return {}
    return json.loads(base64.b64decode(match.group(1)))


def _get_form_params(text: str) -> dict:
    """Extract the GOSS form session parameters from a page."""
    nonce = re.search(rf'"{FORM_NAME}_NONCE" value="([\w-]+)"', text)
    sessionid = re.search(rf'"{FORM_NAME}_SESSIONID" value="([\w-]+)"', text)
    pagesessionid = re.search(rf'"{FORM_NAME}_PAGESESSIONID" value="([\w-]+)"', text)
    return {
        "nonce": nonce.group(1) if nonce else "",
        "sessionid": sessionid.group(1) if sessionid else "",
        "pagesessionid": pagesessionid.group(1) if pagesessionid else "",
    }


def _get_url_params(url: str) -> dict:
    """Extract pageSessionId and fsn from a URL."""
    psi = re.search(r"pageSessionId=([\w-]+)", url)
    fsn = re.search(r"fsn=([\w-]+)", url)
    return {
        "pagesessionid_url": psi.group(1) if psi else "",
        "fsn_url": fsn.group(1) if fsn else "",
    }


class Source:
    def __init__(self, postcode: str, property: str = ""):
        self._postcode = postcode
        self._property = property

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        # Step 1: Load initial form page to get session tokens
        r1 = session.get(FORM_URL, timeout=30)
        r1.raise_for_status()

        url_params1 = _get_url_params(r1.url)
        form_params1 = _get_form_params(r1.text)
        psi1 = re.search(r"pageSessionId=([\w-]+)", r1.text)

        submission_url1 = (
            f"https://www.boston.gov.uk/apiserver/formsservice/http/processsubmission"
            f"?pageSessionId={psi1.group(1) if psi1 else url_params1['pagesessionid_url']}"
            f"&fsid={form_params1['sessionid']}"
            f"&fsn={form_params1['nonce']}"
        )

        # Step 2: Submit search form with postcode and property number
        data2 = {
            f"{FORM_NAME}_PAGESESSIONID": form_params1["pagesessionid"],
            f"{FORM_NAME}_SESSIONID": form_params1["sessionid"],
            f"{FORM_NAME}_NONCE": form_params1["nonce"],
            f"{FORM_NAME}_VARIABLES": "",
            f"{FORM_NAME}_PAGENAME": "COLLECTIONS",
            f"{FORM_NAME}_PAGEINSTANCE": "0",
            f"{FORM_NAME}_COLLECTIONS_SEARCHPROPERTYNAMENUMBER": self._property,
            f"{FORM_NAME}_COLLECTIONS_SEARCHPOSTCODE": self._postcode,
            f"{FORM_NAME}_FORMACTION_NEXT": f"{FORM_NAME}_COLLECTIONS_START10",
        }

        r2 = session.post(
            submission_url1,
            data=data2,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
            timeout=30,
        )
        r2.raise_for_status()

        sv2 = _decode_sv(r2.text)
        addr_options = sv2.get("ADDRESSUPRN_OPTIONDATA", {}).get("value", [])

        # Filter out placeholder entries (empty UPRN / "Select address")
        valid_options = [
            a
            for a in addr_options
            if a[0] and str(a[0]).strip() and a[1] != "Select address"
        ]

        if not valid_options:
            raise ValueError(
                f"No addresses found for postcode '{self._postcode}' "
                f"and property '{self._property}'. "
                "Please check your postcode and property name/number."
            )

        # Use first matching address
        uprn = valid_options[0][0]

        url_params2 = _get_url_params(r2.url)
        form_params2 = _get_form_params(r2.text)

        submission_url2 = (
            f"https://www.boston.gov.uk/apiserver/formsservice/http/processsubmission"
            f"?pageSessionId={url_params2['pagesessionid_url']}"
            f"&fsid={form_params2['sessionid']}"
            f"&fsn={url_params2['fsn_url']}"
        )

        # Step 3: Select address by UPRN to get collection data
        data3 = {
            f"{FORM_NAME}_PAGESESSIONID": form_params2["pagesessionid"],
            f"{FORM_NAME}_SESSIONID": form_params2["sessionid"],
            f"{FORM_NAME}_NONCE": form_params2["nonce"],
            f"{FORM_NAME}_VARIABLES": "",
            f"{FORM_NAME}_PAGENAME": "ADDRESS",
            f"{FORM_NAME}_PAGEINSTANCE": "0",
            f"{FORM_NAME}_ADDRESS_FIELD1034": "false",
            f"{FORM_NAME}_ADDRESS_FIELD1036": "false",
            f"{FORM_NAME}_ADDRESS_FIELD1041": "true",
            f"{FORM_NAME}_ADDRESS_FIELD1042": "false",
            f"{FORM_NAME}_ADDRESS_ADDRESSUPRN": str(uprn),
            f"{FORM_NAME}_FORMACTION_NEXT": f"{FORM_NAME}_ADDRESS_NEXT3",
        }

        r3 = session.post(
            submission_url2,
            data=data3,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            allow_redirects=True,
            timeout=30,
        )
        r3.raise_for_status()

        sv3 = _decode_sv(r3.text)
        collections_data = sv3.get("collectionsData", {}).get("value", {})

        if not collections_data.get("success"):
            raise ValueError(
                f"Failed to retrieve collection data for UPRN {uprn}. "
                "The council website may be temporarily unavailable."
            )

        jobs = collections_data.get("jobs", [])
        entries = []
        for job in jobs:
            next_date_str = job.get("NextDate")
            if not next_date_str:
                continue
            try:
                next_date = datetime.strptime(next_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            bin_type = job.get("Type", "").lower()
            title = job.get("Title", bin_type)
            icon = ICON_MAP.get(bin_type)

            entries.append(Collection(date=next_date, t=title, icon=icon))

        return entries
