import datetime
import re

import requests
from waste_collection_schedule import Collection

TITLE = "Norwich City Council"
DESCRIPTION = "Source for norwich.gov.uk"
URL = "https://www.norwich.gov.uk"
TEST_CASES = {
    "1 Stuart Road": {"uprn": "100090924499"},
}

API_URL = "https://maps.norwich.gov.uk/arcgis/rest/services/MyNorwich/PropertyDetails/FeatureServer/3/query"
COLLECTION_TYPES = {
    "waste and food waste": {
        "title": "Waste and Food Waste",
        "icon": "mdi:trash-can",
    },
    "recycling and food waste": {
        "title": "Recycling and Food Waste",
        "icon": "mdi:recycle",
    },
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self) -> list[Collection]:
        params = {
            "f": "json",
            "where": f"UPRN='{self._uprn}' or UPRN='0{self._uprn}'",
            "outFields": "WasteCollectionHtml",
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        features = response.json()["features"]

        if len(features) != 1:
            raise Exception(f"Expected 1 feature, got {len(features)}")

        html = features[0]["attributes"]["WasteCollectionHtml"]

        date_match = re.search(r"Your next collection: <strong>(.*?)</strong>", html)
        if not date_match:
            raise Exception("No collection date found")
        date_str = date_match.group(1)
        type_match = re.search(r"We will be collecting: <strong>(.*?).</strong>", html)
        if not type_match:
            raise Exception("No collection type found")
        type_str = type_match.group(1)

        date = datetime.datetime.strptime(date_str, "%d/%m/%Y").date()

        type = COLLECTION_TYPES.get(type_str) or {}

        entries = [
            Collection(
                date=date,
                t=type["title"],
                icon=type["icon"],
            ),
        ]

        return entries
