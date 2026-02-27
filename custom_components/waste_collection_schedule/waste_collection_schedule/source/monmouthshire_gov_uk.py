from datetime import date, datetime
import logging
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentException

_LOGGER = logging.getLogger(__name__)

TITLE = "Monmouthshire Council"
DESCRIPTION = "Source for Monmouthshire Council, UK."
URL = "https://www.monmouthshire.gov.uk"

COUNTRY = "uk"

TEST_CASES = {
    "200000952833": {"uprn": 200000952833},
    "10033354474": {"uprn": 10033354474},
    "10033351693": {"uprn": 10033351693},
}

API_URL = "https://maps.monmouthshire.gov.uk/localinfo.aspx"

ICON_MAP = {
    "Blue food bin": "mdi:food",
    "Garden Waste Bins": "mdi:leaf",
    "Green Glass Box": "mdi:glass-fragile",
    "Household rubbish bag": "mdi:trash-can",
    "Red & purple recycling bags": "mdi:recycling",
    "Yellow nappy & hygiene waste bag": "mdi:diaper-outline",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting [Find My Address](https://www.findmyaddress.co.uk) and entering in your address details.",
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
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

        if not self._uprn.isdigit():
            raise SourceArgumentException(self._uprn, "UPRN must be numeric")

    def _parse_collection_date(self, collection_date_str: str) -> date | None:
        """Convert a date string without a year into the next valid future date."""

        cleaned_date = " ".join(
            re.sub(r'(\d+)(st|nd|rd|th)', r'\1', collection_date_str).split()
        )

        # Find Date & Month in String
        match = re.search(r"(\d{1,2})\s+([A-Za-z]+)", cleaned_date)
        if not match:
            return None

        # Extract Day & Month
        try:
            day = int(match.group(1))
            month = datetime.strptime(match.group(2), "%B").month

        except ValueError:
            return None

        today = date.today()

        # Handles dates spanning years, i.e. Dec to Jan, due to no year in source
        for year in (today.year, today.year + 1):
            try:
                date_temp = date(year, month, day)
                
                # Handles 29 Feb on non-leap year
                if date_temp >= today:
                    return date_temp

            except ValueError:
                continue

        return None

    def fetch(self) -> list[Collection]:
        try:
            r = requests.get(
                API_URL, 
                params={"action":"SetAddress", "UniqueId":self._uprn,}, 
                headers=HEADERS,
                timeout=30
                )

            r.raise_for_status()

        # Check for Website Errors
        except requests.RequestException as e:
            raise SourceArgumentException(self._uprn, "Monmouthshire Council website unreachable") from e

        soup = BeautifulSoup(r.text, "html.parser")

        uprn_check = soup.find("b", string="Unique Property Reference Number (UPRN):")

        # Check to see if UPRN text is on page
        if not uprn_check or not uprn_check.next_sibling:
            raise SourceArgumentException(
                self._uprn,
                f"UPRN {self._uprn} is invalid or outside the Monmouthshire Council area. Make sure your address returns entries on the council website: {API_URL}"
            )

        # Check UPRN provided & UPRN on page match
        if uprn_check.next_sibling.strip() != str(self._uprn):
            raise SourceArgumentException(
                self._uprn,
                f"UPRN {self._uprn} does not match UPRN provided."
            )

        entries = []

        # Find div for the Waste Collections section
        waste_div = soup.find("div", attrs={"aria-label": "Waste Collections"})

        if waste_div:
            waste_blocks = waste_div.find_all("div", class_="waste")

            for waste_block in waste_blocks:

                # Get location of <h4> for Waste Type and <strong> for Collection Date
                waste_h4 = waste_block.find("h4")
                collection_strong = waste_block.find("strong")

                if waste_h4 and collection_strong:
                    waste_type = " ".join(waste_h4.get_text().split())
                    # Remove unwanted part of title
                    waste_type = waste_type.replace(" (pay to use service)", "")

                    collection_date_text = collection_strong.get_text(strip=True)

                    collection_date = self._parse_collection_date(collection_date_text)

                    if not collection_date:
                        _LOGGER.warning(
                            "Unable to parse %r with date %r.",
                            waste_type,
                            collection_date_text,
                        )
                        continue

                    entries.append(
                        Collection(
                            date = collection_date,
                            t = waste_type,
                            icon = ICON_MAP.get(waste_type, "mdi:trash-can"),
                        )
                    )

        if not entries:
            raise SourceArgumentException(self._uprn, "No collection dates found in response.")

        return entries
