import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Dorset Council"
DESCRIPTION = "The local authority for the non-metropolitan county of Dorset in England"
URL = "https://www.dorsetcouncil.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": 100040606062},
    "Test_002": {"uprn": "100040606087"},
    "Test_003": {"uprn": "100040606071"},
}
ICON_MAP = {
    "Recycling": "mdi:recycle",
    "Rubbish": "mdi:trash-can",
    "Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food",
}

API_URLS = {
    "Recycling": "https://geoapi.dorsetcouncil.gov.uk/v1/Services/recyclingday/{uprn}",
    "Rubbish": "https://geoapi.dorsetcouncil.gov.uk/v1/Services/refuseday/{uprn}",
    "Garden Waste": "https://geoapi.dorsetcouncil.gov.uk/v1/Services/gardenwasteday/{uprn}",
    "Food Waste": "https://geoapi.dorsetcouncil.gov.uk/v1/Services/foodwasteday/{uprn}",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)

    def fetch(self):
        entries = []
        for bin in API_URLS:
            r = requests.get(API_URLS[bin].format(uprn=self._uprn))
            json_data = json.loads(r.content)

            date = datetime.strptime(json_data['dateNextVisit'], "%m/%d/%Y").date()

            entries.append(
                Collection(
                    date=date,
                    t=bin,
                    icon=ICON_MAP.get(bin),
                )
            )

        return entries
