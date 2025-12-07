
"""
Support for Betzdorf waste collection schedule.

For more details about this platform, please refer to the documentation at
https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/betzdorf_lu.md
"""

from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Betzdorf"
DESCRIPTION = "Source for Betzdorf, Luxembourg waste collection."
URL = "https://www.betzdorf.lu"
TEST_CASES = {
    "Betzdorf": {},
}

ICON_MAP = {
    "centre-de-ressources-recyclingpark-superdreckskescht": "mdi:recycle",
    "dechets-menagers-hausmull-exception": "mdi:trash-can",
    "dechets-biodegradables-biomull-exception": "mdi:leaf",
    "valorlux": "mdi:package-variant",
    "verre-papiers-altglas-altpapier": "mdi:bottle-wine",
}

API_URL = "https://www.betzdorf.lu/fr/waste"


class Source:
    def __init__(self):
        pass

    def fetch(self):
        # Fetch data from API with SSL verification disabled
        # (due to certificate issues with betzdorf.lu website)
        r = requests.get(API_URL, verify=False)
        r.raise_for_status()
        
        data = r.json()
        
        entries = []
        
        for waste_type in data:
            slug = waste_type.get("slug", "")
            title = waste_type.get("title", "")
            dates = waste_type.get("dates", [])
            
            # Get icon based on slug
            icon = ICON_MAP.get(slug, "mdi:trash-can")
            
            # Process each date
            for date_entry in dates:
                date_start = date_entry.get("dateStart")
                if date_start:
                    # Parse the date (format: 2025-11-08T00:00:00)
                    collection_date = datetime.fromisoformat(date_start).date()
                    
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=title,
                            icon=icon,
                        )
                    )
        
        return entries
