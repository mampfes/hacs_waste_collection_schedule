import json
import requests

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "South Tyneside Council"
DESCRIPTION = "Source for southtyneside.gov.uk services for South Tyneside Council, UK."
URL = "https://southtyneside.gov.uk"
HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "Referer": "https://www.southtyneside.gov.uk/article/1023/Bin-collection-dates",
    "User-Agent":"Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/112.0",
}
API = "https://www.southtyneside.gov.uk/apiserver/ajaxlibrary"
TEST_CASES = {
    "Test_001": {"postcode": "NE34 8RY", "uprn": "100000342955"},
    "Test_002": {"postcode": "SR6 7AJ", "uprn": "100000359535"},
    "Test_003": {"postcode": "NE31 1LY", "uprn": 100000304486},
}
ICON_MAP = {
    "HOUSEHOLD": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, postcode, uprn):
        self._postcode = str(postcode).replace(" ","")
        self._uprn = str(uprn).zfill(12)

    def fetch(self):

        s = requests.Session()

        # get uprn and full address for subsequent query
        payload = json.dumps(
            {
                "id": "1682761045902",
                "jsonrpc": "2.0",
                "method": "stc.common.snippets.getAddressList",
                "params": {
                    "localonly": "true",
                    "postcode": self._postcode
                }
            }
        )
        r1 = s.post(API, headers=HEADERS, data=payload)
        json_data = json.loads(r1.text)["result"]["ReturnedList"]
        for item in json_data:
            if self._uprn in item["UPRN"]:
                self._uprn = item["UPRN"]
                self._address = item["Address"]

        # get collection schedule
        payload = json.dumps(
            {
                "id": "1682761056660",
                "jsonrpc": "2.0",
                "method": "stc.waste.collections.getDates",
                "params": {
                    "addresscode": f"{self._uprn}|{self._address}"
                }
            }
        )
        r2 = s.post(API, headers=HEADERS, data=payload)
        json_data = json.loads(r2.text)["result"]["SortedCollections"]
        
        entries = []
        for item in json_data:
            for monthyear in item["Collections"]:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            monthyear["DateofCollection"], "%Y-%m-%dT00:00:00").date(),
                        t=monthyear["TypeClass"],
                        icon=ICON_MAP.get(monthyear["TypeClass"].upper()),
                    )
                )

        return entries

