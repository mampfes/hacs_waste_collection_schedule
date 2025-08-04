from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Eastleigh Borough Council"
DESCRIPTION = "Source for Eastleigh Borough Council."
URL = "https://eastleigh.gov.uk"
TEST_CASES = {
    "100060319000": {"uprn": 100060319000},
    "100060300958": {"uprn": "100060300958"},
    "100060306006": {"uprn": "100060306006"},
    "10009587286": {"uprn": "10009587286"}
}


ICON_MAP = {
    "Paper": "mdi:package-variant",
    "household": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "food": "mdi:food",
    "glass": "mdi:bottle-soda",
    "garden": "mdi:leaf",
}


API_URL = "https://whichb.in/next/"
# API by Will Murphy | https://willmurphy.co.uk/

class Source:
    def __init__(self, uprn: str | int):
        self._uprn = uprn

    def fetch(self):
        apiurl = f"{API_URL}{self._uprn}"

        # Make the API call
        r = requests.get(apiurl)
        r.raise_for_status()

        data = r.json()
        
        entries = []

        for bin_item in data:
            try:
                date = datetime.strptime(bin_item["date"], "%d %b %Y").date()
            except ValueError as e:
                print("Date parsing error:", bin_item["date"], e)
                continue

            name = bin_item["name"]
            icon = next(
                (icon for key, icon in ICON_MAP.items() if key.lower() in name.lower()),
                None,
            )

            entries.append(Collection(date=date, t=name, icon=icon))

        return entries