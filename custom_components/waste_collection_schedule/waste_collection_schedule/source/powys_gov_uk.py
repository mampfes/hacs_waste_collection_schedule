import base64
import json
import re
from datetime import date
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateutil_parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Powys County Council"
DESCRIPTION = "Source for en.powys.gov.uk services for Powys"
URL = "https://en.powys.gov.uk"
FORM_PAGE = f"{URL}/binday"
COUNTRY = "uk"

TEST_CASES = {
    "15 Market Street, Newtown": {
        "postcode": "SY16 2PQ",
        "uprn": "100100307820",
    },
    "3 Brookfields, Llandrindod Wells": {
        "postcode": "LD1 5LF",
        "uprn": "10011732434",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Your property postcode, e.g. SY16 2PQ",
        "uprn": "Your Unique Property Reference Number. Find it at https://www.findmyaddress.co.uk/",
    }
}

ICON_MAP = {
    "bdl-card--refuse": "mdi:trash-can",
    "bdl-card--recycling": "mdi:recycle",
    "bdl-card--garden": "mdi:leaf",
}

WASTE_TYPE_MAP = {
    "bdl-card--refuse": "General Rubbish",
    "bdl-card--recycling": "Recycling and Food Waste",
    "bdl-card--garden": "Garden Waste",
}


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9",
            }
        )

        # Step 1: GET the form page to obtain session tokens and form action
        r = session.get(FORM_PAGE, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        form = soup.find("form", id="BINDAYLOOKUP_FORM")
        if not form or not form.get("action"):
            raise ValueError(
                "Could not find BINDAYLOOKUP_FORM on the Powys bin day page."
            )

        action = form["action"]

        def _val(name: str) -> str:
            el = form.find("input", attrs={"name": name})
            return el["value"] if el and el.has_attr("value") else ""

        page_session_id = _val("BINDAYLOOKUP_PAGESESSIONID")
        session_id = _val("BINDAYLOOKUP_SESSIONID")
        nonce = _val("BINDAYLOOKUP_NONCE")

        # Fallback: extract IDs from action URL query string
        if not (page_session_id and session_id and nonce):
            parsed = urlparse(action)
            qs = parse_qs(parsed.query)
            page_session_id = page_session_id or qs.get("pageSessionId", [""])[0]
            session_id = session_id or qs.get("fsid", [""])[0]
            nonce = nonce or qs.get("fsn", [""])[0]

        # Step 2: POST address lookup with UPRN to get collection dates
        data = {
            "BINDAYLOOKUP_PAGESESSIONID": page_session_id,
            "BINDAYLOOKUP_SESSIONID": session_id,
            "BINDAYLOOKUP_NONCE": nonce,
            "BINDAYLOOKUP_VARIABLES": "",
            "BINDAYLOOKUP_PAGENAME": "ADDRESSLOOKUP",
            "BINDAYLOOKUP_PAGEINSTANCE": "0",
            "BINDAYLOOKUP_ADDRESSLOOKUP_ADDRESSLOOKUPPOSTCODE": self._postcode,
            "BINDAYLOOKUP_ADDRESSLOOKUP_ADDRESSLOOKUP": "0",
            "BINDAYLOOKUP_ADDRESSLOOKUP_POSTALADDRESS": "",
            "BINDAYLOOKUP_ADDRESSLOOKUP_UPRN": self._uprn,
            "BINDAYLOOKUP_FORMACTION_NEXT": (
                "BINDAYLOOKUP_ADDRESSLOOKUP_ADDRESSLOOKUPBUTTONS"
            ),
        }

        r2 = session.post(
            action,
            data=data,
            headers={
                "Origin": URL,
                "Referer": FORM_PAGE,
            },
            timeout=30,
        )
        r2.raise_for_status()

        # Step 3: Extract collection dates from embedded FormData blob
        match = re.search(r'BINDAYLOOKUPFormData = "([^"]+)"', r2.text)
        if not match:
            raise ValueError(
                "Could not find BINDAYLOOKUPFormData in the response. "
                "Check that the postcode and UPRN are correct."
            )

        form_data = json.loads(base64.b64decode(match.group(1)).decode())
        collection_html = form_data.get("COLLECTIONDATES_1", {}).get(
            "COLLECTIONDATES", ""
        )

        if not collection_html:
            raise ValueError(
                "No collection dates found in the response. "
                "Check that the postcode and UPRN are correct."
            )

        return self._parse_collections(collection_html)

    @staticmethod
    def _parse_collections(html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []

        for card_class, waste_type in WASTE_TYPE_MAP.items():
            card = soup.find(
                "div", class_=lambda c, cc=card_class: c and cc in c if c else False
            )
            if not card:
                continue

            for li in card.find_all("li"):
                text = li.get_text(strip=True)
                # Remove any trailing link text in parentheses
                text = re.sub(r"\(.*?\)", "", text).strip()
                # Strip ordinal suffixes: 14th -> 14, 21st -> 21, etc.
                text = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text)
                try:
                    collection_date: date = dateutil_parser.parse(
                        text, dayfirst=True
                    ).date()
                except Exception:
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(card_class),
                    )
                )

        return entries
