from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Eastleigh Borough Council"
DESCRIPTION = "Source for Eastleigh Borough Council."
URL = "https://www.eastleigh.gov.uk"
TEST_CASES = {
    "100060319000": {"uprn": 100060319000},
    "100060300958": {"uprn": "100060300958"},
}


ICON_MAP = {
    "Paper": "mdi:package-variant",
    "household": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "food": "mdi:food",
    "glass": "mdi:bottle-soda",
    "garden": "mdi:leaf",
}


API_URL = "https://www.eastleigh.gov.uk/waste-bins-and-recycling/collection-dates/your-waste-bin-and-recycling-collections"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
        })
        
        args = {"uprn": self._uprn}

        # get json file
        r = s.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        dls = soup.find_all("dl")

        entries = []

        for dl in dls:
            dts = dl.findAll("dt")
            for dt in dts:
                dd = dt.find_next_sibling("dd")
                if not dd:
                    continue

                try:
                    # Mon, 29 Apr 2024
                    date = datetime.strptime(dd.text, "%a, %d %b %Y").date()
                except ValueError:
                    continue

                icon = ICON_MAP.get(
                    dt.text.strip().split(" ")[0].lower()
                )  # Collection icon
                type = dt.text
                entries.append(Collection(date=date, t=type, icon=icon))

        return entries
