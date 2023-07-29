import json
import re
import requests

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Riding of Yorkshire Council"
DESCRIPTION = "Source for East Riding of Yorkshire Council, UK."
URL = "https://eastriding.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "010002364380", "postcode": "DN14 6BJ"},
    "Test_002": {"uprn": "100050020969", "postcode": "YO16 4HF"},
    "Test_003": {"uprn": "100050099708", "postcode": "HU12 0PE"},
    "Test_004": {"uprn": 10002364380, "postcode": " DN146BJ "}
}
ICON_MAP = {
    "BlueDate": "mdi:recycle",
    "GreenDate": "mdi:trash-can",
    "BrownDate": "mdi:leaf",
}
REGEX = {
    "API_KEY": r"APIKey=(.+)&L",
    "LICENSEE": r"Licensee=(.+)&",
}

class Source:
    def __init__(self, uprn, postcode):
        self._uprn = str(uprn).zfill(12)
        self._postcode = str(postcode).strip().replace(" ", "")

    def fetch(self):
        s = requests.Session()

        # get api_key and licensee
        r1 = s.get("https://www.eastriding.gov.uk/templates/eryc_corptranet/js/eryc-bin-checker.js")
        api_key = re.findall(REGEX["API_KEY"], r1.text)[0]
        licensee = re.findall(REGEX["LICENSEE"], r1.text)[0]

        # retrieve schedule
        r2 = s.get(f"https://wasterecyclingapi.eastriding.gov.uk/api/RecyclingData/CollectionsData?APIKey={api_key}&Licensee={licensee}&Postcode={self._postcode}")
        r2_json = json.loads(r2.text)["dataReturned"]

        entries = []

        for item in r2_json:
            if item["UPRN"] == self._uprn:
                for key in ICON_MAP:
                    entries.append(
                        Collection(
                            date=datetime.strptime(item[key], "%Y-%m-%dT00:00:00").date(),
                            t=key.replace("Date", " Bin"), # api doesn't return a waste type, so make one up
                            icon=ICON_MAP.get(key),
                    )
                )

        return entries
