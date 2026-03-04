import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Armagh City Banbridge & Craigavon"
DESCRIPTION = "Source for Armagh City Banbridge & Craigavon."
URL = "https://www.armaghbanbridgecraigavon.gov.uk"
TEST_CASES = {
    "BT667ES": {"address_id": 185622007},
    "BT63 5GY": {"address_id": "187318004"},
}
ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden & Food": "mdi:leaf",
}
API_URL = "https://www.armaghbanbridgecraigavon.gov.uk/resident/binday-result/"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find the parameter of your address using https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/, after selecting your address. The address ID is the number at the end of the URL after `address=`.",
}


class Source:
    def __init__(self, address_id: int):
        self._address_id: int = address_id

    def fetch(self) -> list[Collection]:
        args = {"address": self._address_id}

        # Add headers to avoid being blocked as a bot
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        r = requests.get(API_URL, params=args, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # The new structure uses h2 tags with icons for collection types
        headings = soup.find_all("h2")

        if not headings:
            raise Exception("No headings found while parsing the response HTML.")

        entries = []

        for heading in headings:
            # Get the bin type text from the h2
            heading_text = heading.get_text(strip=True)

            # Skip if not a collection type heading
            if "Collections" not in heading_text:
                continue

            # Clean up the bin type name
            bin_type = heading_text.replace("Collections", "").strip()

            # Skip empty or invalid types
            if not bin_type:
                continue

            icon = ICON_MAP.get(bin_type)

            # Find the parent div with class containing 'col-sm-12'
            parent_div = heading.find_parent(
                "div", class_=lambda x: x and "col-sm-12" in x
            )

            if not parent_div:
                continue

            # Find the next sibling div that contains the dates
            dates_div = parent_div.find_next_sibling(
                "div", class_=lambda x: x and "col-sm-12" in x and "col-md-9" in x
            )

            if not dates_div:
                continue

            # Find all h4 tags containing the dates
            date_elements = dates_div.find_all("h4")

            for date_elem in date_elements:
                date_text = date_elem.get_text(strip=True)

                # The date text includes an icon, so we need to extract just the date
                # Format is typically: "11/11/2025"
                # We need to find the date pattern
                date_match = re.search(r"\d{2}/\d{2}/\d{4}", date_text)

                if date_match:
                    date_str = date_match.group()
                    try:
                        date = datetime.strptime(date_str, "%d/%m/%Y").date()
                        entries.append(Collection(date=date, t=bin_type, icon=icon))
                    except ValueError:
                        # Skip invalid dates
                        continue

        return entries
