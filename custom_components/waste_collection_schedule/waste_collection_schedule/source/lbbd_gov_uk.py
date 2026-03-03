from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

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
    "Green-Garden": {
        "waste_type": "Garden waste",
        "icon": "mdi:grass",
    },
}

API_URL = "https://www.lbbd.gov.uk/rest/bin/{uprn}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        headers = {"user-agent": "Home-Assitant-waste-col-sched/2.11"}

        r = requests.get(API_URL.format(uprn=self._uprn), headers=headers, timeout=30)
        rubbish_data = r.json()

        entries = []

        for result in rubbish_data["results"]:
            collection_type = COLLECTION_MAP.get(
                result["bin_type"],
                {"waste_type": result["bin_type"], "icon": None},
            )

            for collection_date in (
                [result["nextcollection"]] if result["nextcollection"] else []
            ) + result["futurecollections"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(collection_date, "%A %d %B %Y").date(),
                        t=collection_type["waste_type"],
                        icon=collection_type["icon"],
                    )
                )

        return entries
