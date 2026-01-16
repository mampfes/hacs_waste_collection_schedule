from __future__ import annotations

import re
from dataclasses import dataclass
import datetime
from dateutil import parser

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection


TITLE = "Neath Port Talbot Council"
DESCRIPTION = "Source for waste collection services for Neath Port Talbot Council"
URL = "https://www.npt.gov.uk/"


HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "an easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
}


PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}


PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "The postcode of the address to look up (e.g., SA11 1AB).",
        "uprn": "Your Unique Street Reference Number (USRN) can be found by searching for your address at https://uprn.uk/ and viewing the _Data Associations_ section.",
    }
}


TEST_CASES = {
    "Test_001": {
        "postcode": "SA11 3HW",
        "uprn": 100100601042,
    },
    "Test_002": {
        "postcode": "SA11 3HY",
        "uprn": "100100599841",
    },
    "Test_003": {
        "postcode": "SA11 3DY",
        "uprn": "100100600279",
    },
}


ICON_MAP = {
    "Plastic / Tins / Cans": "mdi:bottle-soda",
    "Cardboard, Cartons and Paper": "mdi:package-variant",
    "Glass": "mdi:glass-fragile",
    "Food Waste": "mdi:leaf",
    "Batteries": "mdi:battery",
    "General Household Rubbish": "mdi:trash-can",
    "Garden Waste": "mdi:flower",
}


class FailedToFindTokensError(Exception): ...


class FailedToFindCollections(Exception): ...


_DAY_MONTH_RE = re.compile(
    r"(?i)^\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*,?\s*(\d{1,2})\s*([A-Za-z]+)\s*$"
)


@dataclass(frozen=True)
class Tokens:
    request_verification_token: str | None
    ufprt: str | None


class Source:
    """
    Neath Port Talbot Council waste collection source.

    The Neath Port Talbot Council website is built in a way that makes it very difficult to scrape waste collection
    data.
    Collection dates are only given for the next two weeks from the current date.
    Unfortunately, the user must submit their postcode even if they already know their UPRN.

    This source implementation works by simulating the multi-step form submission process that a user would go
    through on the website:
        1. Load the initial page to obtain necessary tokens.
        2. Submit the postcode to get the list of addresses.
        3. Submit the UPRN to get the waste collection schedule.

    Finally, the waste collection schedule is parsed from the resulting HTML page.
    """
    _BASE_URL = f"{URL}bins-and-recycling/equipment-and-collections/bin-day-finder/"
    _HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Referer": _BASE_URL,
        "Origin": URL,
    }

    def __init__(self, uprn: str | int, postcode: str) -> None:
        self._uprn = str(uprn).zfill(12)
        self._postcode = postcode

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(self._HEADERS)

        # First, make an initial GET request to obtain the necessary tokens.
        initial_request = session.get(self._BASE_URL, timeout=20)
        initial_request.raise_for_status()

        # Step 1: Submit the postcode to get the address list / UPRNs.
        # Note that even if we already know the UPRN, we still need to go through this step.
        fetch_addresses_payload = {
            **_base_post_payload(initial_request.text),
            "PostCode": self._postcode,
            "action": "Find address"
        }
        fetch_addresses_request = session.post(self._BASE_URL, data=fetch_addresses_payload, timeout=20)
        fetch_addresses_request.raise_for_status()

        # Step 2: Submit the UPRN to get the waste collection schedule.
        fetch_collections_payload = {
            **_base_post_payload(fetch_addresses_request.text),
            "Address": self._uprn,
            "action": "Show my bin days"
        }
        fetch_collections_request = session.post(self._BASE_URL, data=fetch_collections_payload, timeout=20)
        fetch_collections_request.raise_for_status()

        # Step 3: Parse the waste collection schedule from the response HTML.
        return _parse_collections_from_page_source(fetch_collections_request.text)


def _base_post_payload(raw_html: str) -> dict[str, str]:
    tokens = _extract_tokens(raw_html)
    return {
        "__RequestVerificationToken": tokens.request_verification_token,
        "ufprt": tokens.ufprt,
    }


def _extract_tokens(raw_html: str) -> Tokens:
    soup = BeautifulSoup(raw_html, "html.parser")

    try:
        request_verification_token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]
    except TypeError as e:
        raise FailedToFindTokensError("Failed to find __RequestVerificationToken in HTML.") from e

    try:
        ufprt = soup.find("input", {"name": "ufprt"})["value"]
    except TypeError as e:
        raise FailedToFindTokensError("Failed to find ufprt in HTML.") from e

    return Tokens(
        request_verification_token=request_verification_token,
        ufprt=ufprt,
    )


def _parse_collections_from_page_source(raw_html: str) -> list[Collection]:
    soup = BeautifulSoup(raw_html, "html.parser")
    root = soup.find(id="contentInner")

    # Find all date headers (they are <h2> containing e.g. "Thursday, 23 October").
    headers = [h for h in root.find_all("h2") if _DAY_MONTH_RE.match(_clean_text(h.get_text()))]

    collections: list = []
    for h2 in headers:
        collection_date = _collection_date_from_header(h2.get_text())

        for sib in h2.next_siblings:
            name = sib.name
            if not name:
                continue

            if name == "h2":
                # We've finished iterating this date's collections, so break to loop to the next date header.
                break

            cards = sib.find_all(class_="card") or []
            for card in cards:
                a = card.find("a")
                if not a:
                    continue

                type_text = _clean_text(a.get_text())
                if not type_text:
                    continue

                collections.append(
                    Collection(
                        date=collection_date,
                        t=type_text,
                        icon=ICON_MAP.get(type_text),
                    )
                )

    if not collections:
        raise FailedToFindCollections("No waste collection entries found on page.")

    return collections


def _collection_date_from_header(raw_html: str) -> datetime.date:
    """
    Parse a datetime from a header like 'Thursday, 23 October'.
    """
    return parser.parse(_clean_text(raw_html), dayfirst=True, fuzzy=True).date()


def _clean_text(s: str) -> str:
    return " ".join(s.replace("\xa0", " ").split())
