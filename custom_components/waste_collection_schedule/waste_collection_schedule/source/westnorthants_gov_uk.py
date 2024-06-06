from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Northamptonshire council"
DESCRIPTION = "Source for West Northamptonshire council."
URL = "https://www.westnorthants.gov.uk/"
TEST_CASES = {
    "28058314": {"uprn": 28058314},
    "15049111": {"uprn": "15049111"},
}


ICON_MAP = {
    "refuse": "mdi:trash-can",
    "food": "mdi:food",
    "garden": "mdi:recycle",
    "recycling": "mdi:package-variant",
    "recycling_boxes": "mdi:package-variant",
    "sacks": "mdi:sack",
}


API_URL = (
    "https://api.westnorthants.digital/openapi/v1/unified-waste-collections/{uprn}"
)


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        # Get variables for workings
        response = requests.get(
            API_URL.format(uprn=self._uprn),
        )
        response.raise_for_status()
        data = response.json()

        entries = []

        for collection in data["collectionItems"]:
            day = datetime.strptime(collection["date"], "%Y-%m-%d").date()
            entries.append(
                Collection(
                    t=collection["type"],
                    date=day,
                    icon=ICON_MAP.get(collection["type"]),
                )
            )

        return sorted(entries, key=lambda x: x.date)
