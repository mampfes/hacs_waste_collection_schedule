import requests
from bs4 import BeautifulSoup
from datetime import datetime

from waste_collection_schedule import Collection

TITLE = "SIDEC"
DESCRIPTION = "Source for SIDEC waste collection."
URL = "https://www.sidec.lu"
TEST_CASES = {
    "Parc Hosingen": {"commune_id": "PLEASE_REPLACE_ME"}, # Replace with the correct ID
}

API_URL = "https://www.sidec.lu/fr/Collectes/Calendrier"
ICON_MAP = {
    "BULKY": "mdi:wardrobe",
    "GLASS": "mdi:bottle-wine",
    "ORGANIC": "mdi:leaf",
    "PAPER": "mdi:newspaper-variant-multiple-outline",
    "RESIDUAL": "mdi:trash-can",
}

# As found in the luxwastecalendar project
# It notes a bug in the Sidec HTML source where GLASS and ORGANIC are inverted
WASTE_MAPPING = {
    "encombrants": "BULKY",
    "verre": "ORGANIC",
    "dechets organiques": "GLASS",
    "papiers cartons": "PAPER",
    "dechets menagers": "RESIDUAL"
}


class Source:
    def __init__(self, commune_id):
        self._commune_id = commune_id

    def fetch(self):
        now = datetime.now()
        year = now.year

        collections = []

        # Fetch for current year
        collections.extend(self._fetch_year(year))

        # If we are in the last quarter of the year, fetch next year's calendar as well if available
        if now.month >= 10:
            try:
                collections.extend(self._fetch_year(year + 1))
            except Exception:
                # Next year's calendar might not be available yet
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
                if not src:
                    continue
                
                # Extract info from filename, e.g. /extension/sidec/design/sidec/images/calendar/caption-dechets_menagers/caption-dechets_menagers-16.gif
                try:
                    filename = src.split("/")[-1]
                    parts = filename.replace(".gif", "").split("-")
                    day = int(parts[-1])
                    waste_type_str = parts[0].replace("caption_", "").replace("_", " ")
                    
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
                    # Ignore images that don't match the expected format
                    continue
        
        return collections
