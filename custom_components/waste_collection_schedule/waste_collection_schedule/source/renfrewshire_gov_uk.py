from urllib.parse import parse_qs, urlparse

import requests, json
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Renfrewshire Council"
DESCRIPTION = "Source for renfrewshire.gov.uk services for Renfrewshire"
URL = "https://renfrewshire.gov.uk/"
API_URL = "https://www.renfrewshire.gov.uk/bins-and-recycling/bin-collection/bin-collection-calendar/check-your-bin-collection-day/view/"

TEST_CASES = {
    "Test_001": {"uprn": 123033059},
    "Test_002": {"uprn": "123034174"},
    "Test_003": {"uprn": "123046497"},
}

ICON_MAP = {
    "Grey": "mdi:trash-can",
    "Brown": "mdi:leaf",
    "Green": "mdi:glass-fragile",
    "Blue": "mdi:note",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        url = "https://www.renfrewshire.gov.uk/bins-and-recycling/bin-collection/bin-collection-calendar/check-your-bin-collection-day/view/" + self._uprn
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        }

        r = requests.get(url, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        collections_data = soup.find("script", {"type": "application/json", "id": "collections-data"})

        entries = []

        if collections_data:
            try:
                # Get the text content and parse JSON
                binData = json.loads(collections_data.string.strip())
            except json.JSONDecodeError as e:
                print("JSON Decode Failed with: " + e)
            finally:
                
                for date_str, bins in binData.items():
                    date = datetime.fromisoformat(date_str).date()
                    
                    for bin_name, details in bins.items():
                        if details is None:
                            continue  # skip empty bins
                        
                        collection_type = details["ShortName"]  # e.g. "Blue", "Brown", "Grey"
                        
                        entries.append(
                            Collection(
                                date=date,
                                t=collection_type,
                                icon=ICON_MAP.get(collection_type),
                            )
                        )

        return entries
