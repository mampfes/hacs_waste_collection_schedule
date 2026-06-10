import logging
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Repentigny (QC)"
DESCRIPTION = "Source script for Ville de Repentigny waste collection"
URL = "https://repentigny.ca/services/citoyens/collectes"

TEST_CASES = {
    "Sector A": {"sector": "A"},
    "Sector B": {"sector": "B"},
    "Sector C": {"sector": "C"},
}

ICON_MAP = {
    "Residue": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Organic": Icons.ORGANIC,
    "Bulky": Icons.BULKY,
    "Branches": Icons.GARDEN,
    "ChristmasTree": Icons.CHRISTMAS_TREE,
    "Glass": Icons.GLASS,
    "Paper": Icons.PAPER,
    "Cardboard": Icons.PAPER,
    "Yard Waste": Icons.GARDEN,
    "Hazardous": Icons.HAZARDOUS,
    "Dechets": Icons.GENERAL_WASTE,
    "Résidus": Icons.GENERAL_WASTE,
    "Recyclage": Icons.RECYCLING,
    "Matières organiques": Icons.ORGANIC,
    "Encombrants": Icons.BULKY,
    "Résidus verts": Icons.GARDEN,
    "Sapins": Icons.CHRISTMAS_TREE,
}

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

MONTH_PATTERN = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b"

LOGGER = logging.getLogger(__name__)

PARAM_TRANSLATIONS = {
    "en": {
        "sector": "Sector",
    },
    "fr": {
        "sector": "Secteur",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "sector": "Your waste collection sector (A, B, C, D, E, or F)",
    },
    "fr": {
        "sector": "Votre secteur de collecte des déchets (A, B, C, D, E ou F)",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": 'Enter your sector manually if you know it from the <a href="https://repentigny.ca/services/citoyens/collectes">collection calendar</a>.',
    "fr": 'Entrez votre secteur manuellement si vous le connaissez d\'après le <a href="https://repentigny.ca/services/citoyens/collectes">calendrier de collecte</a>.',
}

COUNTRY = "ca"


class Source:
    def __init__(self, sector: str | None = None):
        self._sector = sector

        # Validate that sector is provided
        if not sector:
            raise ValueError("Sector must be provided")

    def fetch(self):
        """Fetch waste collection schedule for the specified sector."""
        # Use the provided sector directly
        LOGGER.info(f"Using manually provided sector: {self._sector}")
        return self._fetch_by_sector(self._sector)

    def _fetch_by_sector(self, sector):
        """Fetch collection data for a specific sector."""
        # This implementation fetches collection data from the Repentigny
        # municipal website using the identified sector.
        # The sector is used to filter the collection calendar tables on the website.

        # Fetch the collection calendar from the Repentigny website
        response = requests.get(URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        entries = []

        # Find all collection tables
        collection_tables = soup.find_all("table", {"class": "calendrier"})

        for table in collection_tables:
            caption = table.find("caption")
            if not caption:
                continue

            # Extract year and month from caption
            caption_text = caption.text.strip()
            month_match = re.search(r"([A-Za-zÀ-ÿ]+)\s+(\d{4})", caption_text)
            if not month_match:
                continue

            month_name = month_match.group(1)
            year = int(month_match.group(2))

            month_num = MONTHS.get(month_name)
            if not month_num:
                continue

            # Parse table rows
            for row in table.find_all("tr")[1:]:  # Skip header
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                # Check if this cell contains a date
                date_cell = cells[0]
                date_element = date_cell.find("p", {"class": "date"})
                if not date_element or not date_element.text.strip().isdigit():
                    continue

                day = int(date_element.text.strip())

                # Create the date
                try:
                    collection_date = datetime(year, month_num, day).date()
                except ValueError:
                    continue

                # Check if this row belongs to our sector
                # The sector information is typically in the second cell
                info_cell = cells[1]
                if sector not in info_cell.text:
                    continue

                # Parse collection types from the row
                img_container = info_cell.find("p", {"class": "img"})
                if not img_container:
                    continue

                for img in img_container.find_all("img"):
                    collection_type = img.get("title", img.get("alt", "")).strip()
                    if not collection_type:
                        continue

                    # Skip seasonal collections that might not apply to all years
                    if "branches" in collection_type.lower() and month_num not in [
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                    ]:
                        continue

                    # Add collection entry
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=collection_type,
                            icon=ICON_MAP.get(collection_type, Icons.GENERAL_WASTE),
                        )
                    )

        return entries
