import re
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Fylde Council"
DESCRIPTION = "Source for fylde.gov.uk services for Fylde Council, UK."
URL = "https://fylde.gov.uk"
TEST_CASES = {
    "Test1": {"uprn": "100010402452"},
    "Test2": {"uprn": "10013590972"},
    "Test3": {"uprn": 10023481945},
}

API_URL = "https://collectiveview.bartec-systems.com/R152"
API_METHOD = "GetData.ashx"

REGEX_JOB_NAME = r"(?i)Empty Bin\s+(?P<bin_type>\S+(?:\s+\S+)?)"
ICON_MAP = {
    "Grey Bin": "mdi:trash-can",
    "Green Bin": "mdi:leaf",
    "Brown Bin": "mdi:recycle",
    "Blue Bin": "mdi:recycle",
    "Blue Bag": "mdi:recycle",
    "Green Box": "mdi:recycle",
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def _getToken(self, session: requests.Session) -> str:
        # The token required for the API call can only be generated dynamically
        # We generate our own token by loading the "bin collection" web page and scraping it from the relevant iframe
        r = session.get(
            f"{URL}/resident/bins-recycling-and-rubbish/bin-collection-day/"
        )
        r.raise_for_status()

        soup: BeautifulSoup = BeautifulSoup(r.text, "html.parser")
        iframe = soup.find("iframe", id="bartec-iframe")
        if not iframe or not isinstance(iframe, Tag):
            raise Exception("Unexpected response from fylde.gov.uk")

        search_res = re.search(r"(?<=Token=)(.*?)(?=&|$)", str(iframe["src"]))
        if search_res is None:
            raise Exception("Token could not be extracted from fylde.gov.uk")
        token = search_res.group(1)

        if not token:
            raise Exception("Token could not be extracted from fylde.gov.uk")

        return urllib.parse.unquote(token)

    def fetch(self):
        session = requests.Session()

        # Build parameters list and call API `https://collectiveview.bartec-systems.com/R152/GetData.ashx?Method=X&Token=Y&UPRN=Z`
        parameters = {
            "Method": "calendareventsfromtoken",
            "Token": self._getToken(session),
            "UPRN": self._uprn,
        }
        r = session.get(f"{API_URL}/{API_METHOD}", params=parameters)
        r.raise_for_status()

        jobs = r.json()
        if not (len(jobs) > 0 and "title" in jobs[0]):
            raise Exception("Unexpected response from fylde.gov.uk API")

        entries = []
        for job in jobs:
            # "Empty Bin GREY BIN 240L" -> "Grey Bin"
            jobName = (
                re.search(REGEX_JOB_NAME, job["title"])
                .group("bin_type")
                .strip()
                .title()
            )
            # Job 'start' string to epoch. "/Date(1580515199000)/" -> "1580515199000"
            date = job["start"][6:-2]

            entries.append(
                Collection(
                    date=datetime.fromtimestamp(int(date) / 1000).date(),
                    t=jobName,
                    icon=ICON_MAP.get(jobName),
                )
            )

        return entries
