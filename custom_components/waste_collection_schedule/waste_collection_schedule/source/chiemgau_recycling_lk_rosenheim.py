from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Chiemgau Recycling - Landkreis Rosenheim"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for paper waste collection in Landkreis Rosenheim area"  # Describe your source
URL = "https://chiemgau-recycling.de"  # Insert url to service homepage. URL will show up in README.md and info.md
COUNTRY = "de"
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Bruckmühl 1": {
        "district": "Bruckmühl 1"
    }
}

ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Papier": "mdi:package-variant",
}

API_URL = "https://blauetonne.stkn.org/lk_rosenheim"

class Source:
    def __init__(self, district):
        self.district = district

    def fetch(self):
        entries = []

        r = requests.get(f"{API_URL}", params={"district": self.district})
        r.raise_for_status()

        for date in r.json():
            entries.append(
                Collection(
                    date=datetime.fromisoformat(date).date(),  # Collection date
                    t="Papier Tonne",  # Collection type
                    icon=ICON_MAP.get("Papier"),  # Collection icon
                )
            )

        return entries
