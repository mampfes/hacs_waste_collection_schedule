import json
from datetime import datetime
import requests

# Suppress error messages relating to SSLCertVerificationError
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from waste_collection_schedule import Collection  # type: ignore[attr-defined]


TITLE = "Stevenage Borough Council"
DESCRIPTION = "Source for stevenage.gov.uk services for Stevenage, UK."
URL = "https://stevenage.gov.uk"
TEST_CASES = {
    "Coopers Close schedule": {"road": "Coopers Close", "postcode": "SG2 9TL"},
    "Wansbeck Close schedule": {"road": "Wansbeck Close", "postcode": "SG1 6AA"},
    "Chepstow Close schedule": {"road": "Chepstow Close", "postcode": "SG1 5TT"},
}

SEARCH_URLS = {
    "round_search": "https://services.stevenage.gov.uk/~?a=find&v=1&p=P1&c=P1_C33_&act=P1_A43_",
    "collection_search": "https://services.stevenage.gov.uk/~?a=find&v=1&p=P1&c=P1_C37_&act=P1_A64_",
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
}
COLLECTIONS = {"Rubbish", "Recycling"}


class Source:
    def __init__(self, road, postcode):
        self._road = road
        self._postcode = postcode

    def fetch(self):

        s = requests.Session()

        # Get Round ID and Round Code
        # Don't fully understand significance of all of the fields, but API borks if they are not present
        roundData = {
            "data": {
                "fields": ["P1_C31_", "P1_C31_", "P1_C105_", "P1_C105_"],
                "rows": [[self._road, self._road, self._postcode, self._postcode]],
            },
            "sequence": 1,
        }

        headers = {"Content-type": "application/json", "Accept": "text/plain"}
        roundRequest = s.post(
            SEARCH_URLS["round_search"], data=json.dumps(roundData), headers=headers, verify=False
        )
        roundJson = json.loads(roundRequest.text)

        # Get collection info
        collectionData = {
            "data": {
                "fields": [
                    "P1_C37_.selectedRowData.id",
                    "P1_C37_.selectedRowData.roundCode",
                ],
                "rows": [[roundJson["rows"][0][0], roundJson["rows"][0][2]]],
            },
            "sequence": 1,
            "childQueries": [
                {
                    "data": {
                        "fields": ["P1_C37_.selectedRowData.id"],
                        "rows": [[roundJson["rows"][0][0]]],
                    },
                    "index": 0,
                }
            ],
        }

        collectionRequest = s.post(
            SEARCH_URLS["collection_search"],
            data=json.dumps(collectionData),
            headers=headers,verify=False
        )
        collectionJson = json.loads(collectionRequest.text)

        entries = []
        for collection in collectionJson["rows"]:
            if collection[2] == "Recycling collection":
                entries.append(
                    Collection(
                        date=datetime.strptime(collection[1], "%d/%m/%Y").date(),
                        t="Recycling",
                        icon=ICON_MAP.get("RECYCLING"),
                    )
                )
            elif collection[2] == "Refuse collection":
                entries.append(
                    Collection(
                        date=datetime.strptime(collection[1], "%d/%m/%Y").date(),
                        t="Refuse",
                        icon=ICON_MAP.get("REFUSE"),
                    )
                )

        return entries
