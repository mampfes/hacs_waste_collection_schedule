import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "London Borough of Harrow"
DESCRIPTION = "Source for London Borough of Harrow."
URL = "https://www.harrow.gov.uk/"
TEST_CASES = {
    "1 Dudley Gardens": {"uprn": "100021261713"},
    "FLAT 3, 12, LOWER ROAD, HARROW, HA2 0DA": {"uprn": 10070270427},
}

COLLECTION_MAP = {
    "RESIDUAL": {
        "waste_type": "General waste",
        "icon": "mdi:trash-can",
    },
    "GARDEN": {
        "waste_type": "Garden waste",
        "icon": "mdi:leaf",
    },
    "RECYCLABLES": {
        "waste_type": "Recycling waste",
        "icon": "mdi:recycle",
    },
    "FOOD": {
        "waste_type": "Food waste",
        "icon": "mdi:food",
    },
}

API_URL = "https://www.harrow.gov.uk/ajax/bins?u={uprn}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn).zfill(12)

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        rubbish_data = json.loads(r.content)

        entries = []

        for next_collection in rubbish_data["results"]["collections"]["next"]:
            collection_type = COLLECTION_MAP[next_collection["binType"]]
            collection_date = next_collection["eventTime"]
            entries.append(
                Collection(
                    date=datetime.datetime.fromisoformat(collection_date).date(),
                    t=collection_type["waste_type"],
                    icon=collection_type["icon"],
                )
            )

        return entries
