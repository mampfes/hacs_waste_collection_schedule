import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentRequiredWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "SIDEC"
DESCRIPTION = "Source for SIDEC waste collection."
URL = "https://www.sidec.lu"
TEST_CASES = {
    "Parc Hosingen": {"commune": "Parc Hosingen (36777)"},
    "Mersch": {"commune": "Mersch (2611)"},
    "Invalid Commune": {"commune": "Invalid (12345)"},
}

API_URL = "https://www.sidec.lu/fr/Collectes/Calendrier"
ICON_MAP = {
    "BULKY": "mdi:wardrobe",
    "GLASS": "mdi:bottle-wine",
    "ORGANIC": "mdi:leaf",
    "PAPER": "mdi:newspaper-variant-multiple-outline",
    "RESIDUAL": "mdi:trash-can",
}

WASTE_MAPPING = {
    "encombrants": "BULKY",
    "verre": "ORGANIC",
    "dechets organiques": "GLASS",
    "papiers cartons": "PAPER",
    "dechets menagers": "RESIDUAL"
}


class Source:
    def __init__(self, commune: str | None = None):
        self._commune = commune
        self._commune_id: str | None = None
        if commune:
            # Parse the ID from the formatted string, e.g., "Parc Hosingen (36777)"
            match = re.search(r"\((\d+)\)", commune)
            if match:
                self._commune_id = match.group(1)

    def fetch(self):
        if not self._commune or not self._commune_id:
            # Step 1: No commune provided, fetch list from website and raise exception
            r = requests.get(API_URL)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            select = soup.find("select", {"name": "myCommune"})
            if not select:
                raise Exception("Could not find commune dropdown on SIDEC website.")
            
            suggestions = []
            for option in select.find_all("option"):
                if option.get("value"):
                    name = option.text.strip()
                    commune_id = option["value"]
                    suggestions.append(f"{name} ({commune_id})")
            
            raise SourceArgumentRequiredWithSuggestions("commune", sorted(suggestions))

        # If commune was provided but ID could not be parsed, raise error
        # This happens if user enters a free-text value not from the dropdown
        if not self._commune_id:
            raise Exception(f"Invalid commune format: \"{self._commune}\". Please select an entry from the dropdown list.")

        # --- Proceed with fetching data ---
        now = datetime.now()
        year = now.year

        collections = []
        collections.extend(self._fetch_year(year))

        if now.month >= 10:
            try:
                collections.extend(self._fetch_year(year + 1))
            except Exception:
                pass

        return collections

    def _fetch_year(self, year):
        params = {"annee": year, "myCommune": self._commune_id}
        r = requests.get(API_URL, params=params)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        collections = []

        calendar_months = soup.select("#col-2 .calendar")
        for month_index, month_div in enumerate(calendar_months):
            month = month_index + 1
            day_images = month_div.select(".calendar-day img")
            for img in day_images:
                src = img.get("src", "")
                if "caption-" not in src:
                    continue
                
                try:
                    item = src.split("caption-")[-1].split(".gif")[0]
                    day_str = item.split("-")[-1]
                    day = int(day_str)
                    waste_type_str = "-".join(item.split("-")[:-1]).replace("_", " ")
                    date = datetime(year, month, day).date()
                    waste_type = WASTE_MAPPING.get(waste_type_str)
                    if waste_type:
                        collections.append(
                            Collection(
                                date=date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
                except (ValueError, IndexError):
                    continue
        
        return collections
