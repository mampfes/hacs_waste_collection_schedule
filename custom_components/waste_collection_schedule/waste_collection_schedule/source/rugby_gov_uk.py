import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rugby Borough Council"
DESCRIPTION = "Source for Rugby Borough Council, UK."
URL = "https://www.rugby.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 100070200377},
    "Test_002": {"uprn": "100070200372"},
    "Test_003": {"uprn": "010010521297"},
}
ICON_MAP = {
    "Blue-lid recycling bins": "mdi:recycle",
    "Black rubbish bins": "mdi:trash-can",
    "Green garden waste bins": "mdi:leaf",
}

# endpoint and api key based on rugby iOS app
API_URL = "https://apps.cloud9technologies.com/rugby/citizenmobile/mobileapi/wastecollections/{uprn}"
API_KEY = "Y2xvdWQ5OmlkQmNWNGJvcjU="


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        headers = {"Authorization": f"Basic {API_KEY}"}
        r = requests.get(API_URL.format(uprn=self._uprn), headers=headers)

        json_data = json.loads(r.content)
        containers = json_data.get("WasteCollectionDates", {})
        entries = []

        # api returns 8 "containers" which may contain collections
        for i in range(1, 9):
            container = containers.get(f"Container{i}CollectionDetails")
            if container and container.get("CollectionDate"):
                date = datetime.strptime(
                    container.get("CollectionDate"), "%Y-%m-%dT%H:%M:%S"
                ).date()
                desc = container.get("ContainerDescription")
                entries.append(
                    Collection(
                        date=date,
                        t=desc,
                        icon=ICON_MAP.get(desc, "mdi:trash-can"),
                    )
                )

        return entries
