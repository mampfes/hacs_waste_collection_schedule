import datetime
import logging

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

_LOGGER = logging.getLogger(__name__)

TITLE = "Wandsworth Council"
DESCRIPTION = "Source for Wandsworth Council for the London Borough of Wandsworth, UK."
URL = "https://www.wandsworth.gov.uk"

COUNTRY = "uk"

TEST_CASES = {
    "100022659217": {"uprn": 100022659217},
    "100022611611": {"uprn": 100022611611},
    "10091501435": {"uprn": "10091501435"},
}

API_URL = "https://www.wandsworth.gov.uk/my-property/"

ICON_MAP = {
    "Food waste": "mdi:food",
    "Recycling": "mdi:recycling",
    "Rubbish": "mdi:trash-can",
    "Rubbish/Garden waste": "mdi:trash-can",
    "Small electrical items": "mdi:blender",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering your address details."
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.5",
    "Referer": "https://www.wandsworth.gov.uk",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

        if not self._uprn.isdigit():
            raise SourceArgumentException(self._uprn, "UPRN must be numeric")

    def fetch(self) -> list[Collection]:

        try:
            # Wandsworth site can be slow; using a 90s timeout to avoid false failures
            r = requests.get(
                API_URL,
                params={"UPRN": self._uprn, "propertyidentified": "Select"},
                headers=HEADERS,
                timeout=90,
            )

            r.raise_for_status()

        # Check for Website Errors
        except requests.RequestException as e:
            raise SourceArgumentException(
                self._uprn, "Wandsworth Council website unreachable"
            ) from e

        soup = BeautifulSoup(r.text, "html.parser")

        # Check for unexpected page My Property H1
        if not soup.find("h1", string="My Property"):
            raise SourceArgumentException(
                self._uprn, "Unexpected page content from Wandsworth Council"
            )

        # Check if UPRN is correct by if Results Div is returned
        if not soup.find("div", id="result"):
            raise SourceArgumentException(
                self._uprn,
                f"UPRN {self._uprn} is invalid or outside the Wandsworth Council area. Make sure your address returns entries on the council website: {API_URL}",
            )

        # Find the heading for the Rubbish & Recycling section
        rubbish_heading = soup.find(
            "h3", string=lambda text: text and "Rubbish and recycling" in text
        )

        if rubbish_heading:
            # Look for the next <p> sibling immediately after the heading
            next_p = rubbish_heading.find_next_sibling("p")

            # Check to see if source data currently unavailable
            if next_p and "currently unavailable" in next_p.get_text():
                raise SourceArgumentException(
                    self._uprn, "Source data currently unavailable."
                )

        entries = []

        waste_headings = soup.find_all("h4", class_="collection-heading")

        for waste_heading in waste_headings:
            # Get Waste Type from Heading Name
            waste_type = waste_heading.get_text(strip=True)

            #  Navigate to Next Div
            collections = waste_heading.find_next_sibling("div", class_="collections")

            if not collections:
                continue

            for collection in collections.find_all("div", class_="collection"):
                # Remove Strong Element
                strong = collection.find("strong")
                if strong:
                    strong.extract()

                # Remove Completed Badge
                badge = collection.find("span", class_="badge")
                if badge:
                    badge.extract()

                # Extracted Date String
                date_str = collection.get_text(strip=True)

                # Format Date String
                try:
                    collection_date = datetime.datetime.strptime(
                        date_str, "%A %d %B %Y"
                    ).date()

                except ValueError:
                    _LOGGER.warning(
                        "Source date format not recognised. Unable to parse %s date: %r",
                        waste_type,
                        date_str,
                    )
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )

        if not entries:
            raise Exception("No collection dates found in response.")

        return entries
