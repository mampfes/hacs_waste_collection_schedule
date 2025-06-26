import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Swindon Borough Council"
DESCRIPTION = "Swindon Borough Council, UK - Waste Collection"
URL = "https://www.swindon.gov.uk"
TEST_CASES = {
    "1 Nyland Road": {"uprn": "100121147490"},
    "74 Standen Way": {"uprn": "200002922415"},
    "1 Eastbury Way": {"uprn": "10010424600"},
    "33 Ulysses Road": {"uprn": "10010427033"},
}

ICON_MAP = {
    "Rubbish bin": "mdi:trash-can",
    "Recycling boxes": "mdi:recycle",
    "Garden waste bin": "mdi:leaf",
    "Plastics": "mdi:sack",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def fetch(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        }
        params = {"uprnSubmit": "Yes", "addressList": self._uprn}
        r = requests.post(
            "https://www.swindon.gov.uk/info/20122/rubbish_and_recycling_collection_days",
            params=params,
            headers=headers,
        )
        
        if r.status_code == 403 or "403 Client Error" in r.text:
            raise Exception("Rate limiting or IP ban may be in effect")
        
        r.raise_for_status()

        entries = []
        for results in BeautifulSoup(r.text, "html.parser").find_all(
            "div", class_="bin-collection-content"
        ):

            try:
                recyclingdate = results.find("span", class_="nextCollectionDate")

                if recyclingdate is not None:
                    recyclingtype = results.find("div", class_="content-left").find(
                        "h3"
                    )
                    entries.append(
                        Collection(
                            date=parser.parse(recyclingdate.text, dayfirst=True).date(),
                            t=recyclingtype.text,
                            icon=ICON_MAP.get(recyclingtype.text),
                        )
                    )
            except (StopIteration, TypeError):
                pass
        return entries
