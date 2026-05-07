import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stockport Council"
DESCRIPTION = "Source for bin collection services for Stockport Council, UK.\n Refactored with thanks from the Manchester equivalent"
URL = "https://stockport.gov.uk"
TEST_CASES = {
    "domestic": {"uprn": "100011460157"},
}

ICON_MAP = {
    "Black bin": "mdi:trash-can",
    "Blue bin": "mdi:recycle",
    "Brown bin": "mdi:glass-fragile",
    "Green bin": "mdi:leaf",
}

# Regex pattern to match dates like "Thursday, 14 May 2026" or "14 May 2026"
DATE_PATTERN = re.compile(r"(?:\w+,\s*)?(\d{1,2}\s+\w+\s+\d{4})", re.IGNORECASE)

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):
        r = requests.get(
            f"https://myaccount.stockport.gov.uk/bin-collections/show/{self._uprn}"
        )

        soup = BeautifulSoup(r.text, features="html.parser")

        # Find all bin service items
        bins = soup.find_all("div", {"class": re.compile(r"service-item")})

        entries = []
        for bin_div in bins:
            # Find the bin name from h3 element
            h3 = bin_div.find("h3")
            if not h3:
                continue

            bin_name = h3.get_text(strip=True)
            if "bin" not in bin_name.lower():
                continue

            # Normalize bin name to title case (e.g., "Black bin")
            bin_name = bin_name.capitalize()

            # Search for a date pattern within this bin's section
            bin_text = bin_div.get_text()
            date_match = DATE_PATTERN.search(bin_text)

            if date_match:
                date_string = date_match.group(1)
                try:
                    bin_date = datetime.strptime(date_string, "%d %B %Y").date()
                    entries.append(
                        Collection(
                            date=bin_date,
                            t=bin_name,
                            icon=ICON_MAP.get(bin_name),
                        )
                    )
                except ValueError as e:
                    _LOGGER.warning(
                        "Could not parse date '%s' for %s: %s",
                        date_string,
                        bin_name,
                        e,
                    )
            else:
                _LOGGER.warning("No date found for %s", bin_name)

        return entries
