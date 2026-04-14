import base64
import json
import re
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gosport Borough Council"
DESCRIPTION = "Source for Gosport Borough Council waste collection."
URL = "https://www.gosport.gov.uk"
COUNTRY = "uk"
COLLECTION_URL = "https://www.gosport.gov.uk/refuserecyclingdays"

FORM_NAME = "QUERYWARDSCOLLECTIONSWS"

TEST_CASES = {
    "PO12 4RL, 1 Holland House": {
        "postcode": "PO12 4RL",
        "uprn": "37020212",
    },
    "PO12 2EL, 10 Testcombe Road": {
        "postcode": "PO12 2EL",
        "uprn": "37030710",
    },
}

ICON_MAP = {
    "Domestic Waste Collection Service": "mdi:trash-can",
    "Recycling Waste Collection Service": "mdi:recycle",
    "Garden Waste Collection Service": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Go to https://www.gosport.gov.uk/refuserecyclingdays, enter your postcode, and select your address. The UPRN is the number shown next to your address in the dropdown (also appended at the end of the address text).",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your postcode (e.g. PO12 4RL)",
        "uprn": "The Whitespace property reference number for your address",
    },
}


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode = postcode
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        # Step 1: Get the page and extract GOSS form session IDs
        r = session.get(COLLECTION_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find(id=f"{FORM_NAME}_FORM")
        if not form:
            raise Exception("Could not find GOSS form on page")

        action_url = form["action"]
        goss_ids = self._parse_goss_ids(action_url)

        # Step 2: Search for addresses by postcode
        search_data = {
            f"{FORM_NAME}_PAGESESSIONID": goss_ids["page_session_id"],
            f"{FORM_NAME}_SESSIONID": goss_ids["session_id"],
            f"{FORM_NAME}_NONCE": goss_ids["nonce"],
            f"{FORM_NAME}_VARIABLES": "",
            f"{FORM_NAME}_PAGENAME": "PAGE1",
            f"{FORM_NAME}_PAGEINSTANCE": "0",
            f"{FORM_NAME}_PAGE1_SEARCHED": "NO",
            f"{FORM_NAME}_PAGE1_SEARCHADDRESS": "YES",
            f"{FORM_NAME}_PAGE1_NEXTPAGE": "PAGE2",
            f"{FORM_NAME}_PAGE1_POSTCODE": self._postcode,
            f"{FORM_NAME}_PAGE1_PROPERTY": "",
            f"{FORM_NAME}_PAGE1_REFNO": "",
            f"{FORM_NAME}_PAGE1_UPRN": "",
            f"{FORM_NAME}_FORMACTION_NEXT": f"{FORM_NAME}_PAGE1_GETADDRESSES",
        }
        r = session.post(action_url, data=search_data, allow_redirects=True)
        r.raise_for_status()

        # Parse updated form action URL (nonce changes each submission)
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find(id=f"{FORM_NAME}_FORM")
        if not form:
            raise Exception("Could not find GOSS form after address search")

        action_url = form["action"]
        goss_ids = self._parse_goss_ids(action_url)

        # Step 3: Submit with selected property to get collection results
        variables = {
            "SEARCHREF": self._uprn,
            "SEARCHUPRN": self._uprn,
        }
        encoded_vars = base64.b64encode(json.dumps(variables).encode()).decode()

        submit_data = {
            f"{FORM_NAME}_PAGESESSIONID": goss_ids["page_session_id"],
            f"{FORM_NAME}_SESSIONID": goss_ids["session_id"],
            f"{FORM_NAME}_NONCE": goss_ids["nonce"],
            f"{FORM_NAME}_VARIABLES": encoded_vars,
            f"{FORM_NAME}_PAGENAME": "PAGE1",
            f"{FORM_NAME}_PAGEINSTANCE": "0",
            f"{FORM_NAME}_PAGE1_SEARCHED": "YES",
            f"{FORM_NAME}_PAGE1_SEARCHADDRESS": "NO",
            f"{FORM_NAME}_PAGE1_NEXTPAGE": "PAGE2",
            f"{FORM_NAME}_PAGE1_POSTCODE": self._postcode,
            f"{FORM_NAME}_PAGE1_PROPERTY": self._uprn,
            f"{FORM_NAME}_PAGE1_REFNO": self._uprn,
            f"{FORM_NAME}_PAGE1_UPRN": self._uprn,
            f"{FORM_NAME}_FORMACTION_NEXT": f"{FORM_NAME}_PAGE1_FIELD9",
        }
        r = session.post(action_url, data=submit_data, allow_redirects=True)
        r.raise_for_status()

        return self._parse_collections(r.text)

    def _parse_goss_ids(self, url: str) -> dict:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {
            "page_session_id": params["pageSessionId"][0],
            "session_id": params["fsid"][0],
            "nonce": params["fsn"][0],
        }

    def _parse_collections(self, html: str) -> list[Collection]:
        match = re.search(rf"{FORM_NAME}SerializedVariables\s*=\s*\"([^\"]+)\"", html)
        if not match:
            raise Exception("Could not find serialized variables in response")

        serialized = json.loads(base64.b64decode(match.group(1)))

        if "Recordset1" not in serialized:
            raise Exception("No Recordset1 in response")

        recordset = serialized["Recordset1"]
        value = (
            recordset.get("value", recordset)
            if isinstance(recordset, dict)
            else recordset
        )
        result = value.get("GetCollectionByUprnAndDateResult", value)

        if not result.get("SuccessFlag"):
            raise Exception(
                f"API error: {result.get('ErrorDescription', 'Unknown error')}"
            )

        collections_data = result.get("Collections")
        if not collections_data:
            return []

        collection_list = collections_data.get("Collection", [])
        if isinstance(collection_list, dict):
            collection_list = [collection_list]

        entries = []
        for item in collection_list:
            date = datetime.strptime(item["Date"], "%d/%m/%Y %H:%M:%S").date()
            service = item["Service"]
            icon = ICON_MAP.get(service)
            entries.append(Collection(date=date, t=service, icon=icon))

        return entries
