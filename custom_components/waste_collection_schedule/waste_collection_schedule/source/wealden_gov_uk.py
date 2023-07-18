import requests
import json

from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wealden District Council"
DESCRIPTION = "Source for Wealden City services for Wealden District Council, UK."
URL = "https://www.wealden.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10094620272"},
    "Test_002": {"uprn": "200001678582"},
    "Test_003": {"uprn": 100060120819},
    "Test_004": {"uprn": 100060122306},
}

API_URL = "https://www.wealden.gov.uk/wp-admin/admin-ajax.php"
ICON_MAP = {
    "refuseCollectionDate": "mdi:trash-can",
    "recyclingCollectionDate": "mdi:recycle",
    "gardenCollectionDate": "mdi:leaf",
}

COLLECTIONS = {
    "refuseCollectionDate": "Rubbish",
    "recyclingCollectionDate": "Recycling",
    "gardenCollectionDate": "Garden (if applicable)",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.57",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://wealden.gov.uk",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        # s = requests.Session()
        params = {"action": "wealden_get_collections_for_uprn", "uprn": self._uprn}
        r = requests.post(API_URL, headers=HEADERS, data=params)
        json_data = json.loads(r.text)["collection"]
        entries = []

        for collection in ICON_MAP.keys():
            try:
                entries.append(
                    Collection(
                        datetime.strptime(
                            json_data[collection], "%Y-%m-%dT%H:%M:%S"
                        ).date(),
                        t=COLLECTIONS[collection].title(),
                        icon=ICON_MAP[collection],
                    )
                )
            except ValueError:
                pass  # ignore date conversion errors

        return entries
