import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from datetime import datetime

TITLE = "London Borough of Barking and Dagenham"
DESCRIPTION = "Source for London Borough of Barking and Dagenham."
URL = "https://www.lbbd.gov.uk/"
TEST_CASES = {
    "100 Heathway": {"uprn": "100014033"},
    "40 Porters Avenue": {"uprn": "100024629"},

}

COLLECTION_MAP = {
    "Grey-Household": {
        "waste_type": "General waste",
        "icon": "mdi:trash-can",
    },
    "Brown-Recycling": {
        "waste_type": "Recycling",
        "icon": "mdi:recycle",
    },
}

API_URL = "https://www.lbbd.gov.uk/rest/bin/{uprn}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        r = requests.get(API_URL.format(uprn=self._uprn))
        rubbish_data = json.loads(r.content)

        entries = []

        for next_collection in rubbish_data["results"]:
            collection_type = COLLECTION_MAP[next_collection["bin_type"]]
            collection_date = next_collection["nextcollection"]
            entries.append(
                Collection(
                    date=datetime.strptime(collection_date, "%A %d %B %Y").date(),
                    t=collection_type["waste_type"],
                    icon=collection_type["icon"],
                )
            )

        return entries
