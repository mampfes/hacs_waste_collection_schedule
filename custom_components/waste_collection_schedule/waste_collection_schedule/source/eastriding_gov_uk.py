import json
import re
import requests

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Riding of Yorkshire Council"
DESCRIPTION = "Source for East Riding of Yorkshire Council, UK."
URL = "https://eastriding.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "000151124612"},
    "Test_002": {"uprn": "000151004105"},
    "Test_003": {"uprn": "0151035884"},
    "Test_004": {"uprn": 151170625}
}
ICON_MAP = {
    "BlueDate": "mdi:recycle",
    "GreenDate": "",
    "BrownDate": "",
}
REGEX = {
    "API_KEY": r"APIKey=(.+)&L",
    "LICENSEE": r"Licensee=(.+)&",
}


class Source:
    def __init__(self, uprn, postcode):
        self._uprn = str(uprn).zfill(12)
        self._postcode = str(postcode).strip.replace(" ", "")

    def fetch(self):
        s = requests.Session()

        # get api_key and licensee
        r1 = s.get("https://www.eastriding.gov.uk/environment/bins-rubbish-recycling/bins-and-collections/bin-collection-dates/")
        api_key = re.findall(REGEX["API_KEY"], r1.text)[0]
        licensee = re.findall(REGEX["LICENSEE"], r1.text)[0]

        # retrieve schedule
        r2 = s.get(f"https://wasterecyclingapi.eastriding.gov.uk/api/RecyclingData/CollectionsData?APIKey={api_key}&Licensee={licensee}&Postcode={postcode}")
        r2_json = json.loads(r2.text)["dataReturned"]

        entries = []

        for item in r2_json:
            if item["UPRN"] == self._uprn:
                for key in ICON_MAP:
                    Entries.append(
                        Collection(
                            date=datetime.strptime(item[key], "%Y/%m/%dT00:00:00").date(),
                            t=key.replace("Date", " Bin"),
                            icon=ICON_MAP.get(key),
                    )
                )

        return entries
