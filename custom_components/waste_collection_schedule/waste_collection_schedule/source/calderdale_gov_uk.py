import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Calderdale Council"
DESCRIPTION = "Source for calderdale.gov.uk services for Calderdale Council, UK."
URL = "https://www.calderdale.gov.uk"
TEST_CASES = {
    "Test_1": {"postcode": "OL14 7BX", "uprn": "010010152783"},
    "Test_2": {"postcode": "HX1 3UZ", "uprn": "010006741170"},
}

ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Waste": "mdi:trash-can",
    "Garden waste": "mdi:leaf",
}

API_URL = "https://www.calderdale.gov.uk/environment/waste/household-collections/collectiondayfinder.jsp"


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode = postcode
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        # Make POST request to get collection schedule
        data = {
            "postcode": self._postcode,
            "uprn": self._uprn,
            "gdprTerms": "Yes",
            "privacynoticeid": "323",
            "find": "Show me my collection days",
        }

        response = requests.post(API_URL, data=data)
        response.raise_for_status()

        # Parse HTML response
        soup = BeautifulSoup(response.text, "html.parser")

        # Check if address was found
        address_check = soup.find("p", string=lambda text: text and "Currently showing collection days for:" in text)
        if not address_check:
            raise SourceArgumentNotFoundWithSuggestions(
                "uprn",
                self._uprn,
                "Could not find collection information for the provided UPRN and postcode combination. Please verify both values are correct.",
            )

        entries = []

        # Find the collection table
        collection_table = soup.find("table", {"id": "collection"})
        if not collection_table:
            raise Exception("Could not find collection schedule table in response")

        # Process each row (skip header row)
        rows = collection_table.find("tbody").find_all("tr")
        for row in rows[1:]:  # Skip header row
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # Extract waste type from first cell
            waste_type_cell = cells[0]
            waste_type_strong = waste_type_cell.find("strong")
            if not waste_type_strong:
                continue
            waste_type = waste_type_strong.text.strip()

            # Extract next collection date from third cell
            collection_info_cell = cells[2]
            next_collection_p = collection_info_cell.find("p", string=lambda text: text and "will be your next collection" in text)
            
            if next_collection_p:
                # Extract date from text like "Monday 15 December 2025 will be your next collection."
                date_match = re.search(
                    r"(\w+\s+\d{1,2}\s+\w+\s+\d{4})", next_collection_p.text
                )
                if date_match:
                    date_str = date_match.group(1)
                    # Parse date - format is like "Monday 15 December 2025"
                    # Remove day name and parse
                    date_parts = date_str.split()
                    if len(date_parts) >= 4:
                        # Reconstruct without day name: "15 December 2025"
                        date_str_clean = f"{date_parts[1]} {date_parts[2]} {date_parts[3]}"
                        try:
                            collection_date = datetime.strptime(
                                date_str_clean, "%d %B %Y"
                            ).date()

                            entries.append(
                                Collection(
                                    date=collection_date,
                                    t=waste_type,
                                    icon=ICON_MAP.get(waste_type),
                                )
                            )
                        except ValueError:
                            # Skip if date parsing fails
                            continue

        if not entries:
            raise Exception("No collection dates found in response")

        return entries
