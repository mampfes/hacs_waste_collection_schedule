import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mansfield District Council"
DESCRIPTION = "Source for mansfield.gov.uk services for Mansfield District, UK."
URL = "https://mansfield.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10091487039"},
    "Test_002": {"uprn": "100031399527"},
    "Test_003": {"uprn": 200000666900},
}
ICON_MAP = {
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
    "General": "mdi:trash-can",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Host": "portal.wokingham.gov.uk",
    "Origin": "https://www.mansfield.gov.uk",
    "Referer": "https://www.mansfield.gov.uk/",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        coldate = datetime.strftime(datetime.now(), "%d/%m/%Y")

        s = requests.Session()
        r = s.get(
            f"https://portal.mansfield.gov.uk/MDCWhiteSpaceWebService/WhiteSpaceWS.asmx/GetCollectionByUPRNAndDate?apiKey=mDc-wN3-B0f-f4P&UPRN={self._uprn}&coldate={coldate}",
            headers=HEADERS,
        )
        json_data = json.loads(r.text)["Collections"]

        entries = []
        for item in json_data:
            entries.append(
                Collection(
                    date=datetime.strptime(item["Date"], "%d/%m/%Y %H:%M:%S").date(),
                    t=item["Service"].split(" ")[0],
                    icon=ICON_MAP.get(item["Service"].split(" ")[0].upper()),
                )
            )

        return entries
