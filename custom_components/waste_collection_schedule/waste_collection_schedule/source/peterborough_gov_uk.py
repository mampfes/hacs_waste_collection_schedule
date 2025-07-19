import logging
from time import sleep

import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Peterborough City Council"
DESCRIPTION = "Source for peterborough.gov.uk services for Peterborough"
URL = "https://peterborough.gov.uk"
TEST_CASES = {
    "houseNumber": {"post_code": "PE57AX", "number": 1},
    "houseName": {"post_code": "PE57AX", "name": "CASTOR HOUSE"},
    "houseUprn": {"uprn": "100090214774"},
}
API_URL = "https://report.peterborough.gov.uk/waste"
ICON_MAP = {
    "Empty Bin 240L Black": "mdi:trash-can",
    "Empty Bin 240L Green": "mdi:recycle",
    "Empty Bin 240L Brown": "mdi:leaf",
}
HEADERS = {"user-agent": "Mozilla/5.0"}
BIN_MAP = {
    "Black Bin": "Empty Bin 240L Black",
    "Green Bin": "Empty Bin 240L Green",
    "Brown Bin": "Empty Bin 240L Brown",
}  # convert new bin names to old bin names for compatibility

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = number  # no longer required, but retained for compatibility
        self._name = name  # no longer required, but retained for compatibility
        self._uprn = uprn

    def get_uprn_from_postcode(self, s, pcode):
        # returns the first uprn from a postcode search
        # ensures old configs without a uprn arg still work
        r = s.get(f"https://uprn.uk/postcode/{pcode}")
        soup = BeautifulSoup(r.content, "html.parser")
        cols = soup.find("div", {"class": "threecol"})
        li = cols.find("li")
        pcode_uprn = li.find("a", href=True).text
        _LOGGER.warning(
            f"Used postcode to find an approximate uprn ({pcode_uprn}). Update config with property uprn for more accurate results."
        )
        return pcode_uprn

    def get_postcode_from_uprn(self, s, u):
        # returns the postcode from a uprn search
        # ensures old configs without a postcode arg still work
        r = s.get(f"https://uprn.uk/{u}")
        soup = BeautifulSoup(r.content, "html.parser")
        cols = soup.find_all("p", {"class": "flat nopad small"})
        for item in cols:
            if "Postcode:" in item.text:
                pcode = item.find("a", href=True).text.strip().replace(" ", "")
        return pcode

    def fetch(self):

        s = requests.Session()

        # legacy configs may be missing some details for try and populate them
        if self._uprn is None:
            self._uprn = self.get_uprn_from_postcode(s, self._post_code)
            self._post_code = str(self._post_code.replace(" ", ""))
        if self._post_code is None:
            self._post_code = self.get_postcode_from_uprn(s, self._uprn)

        # visit page to get session cookies
        r = s.get(API_URL, headers=HEADERS)

        # get schedule
        data = {"address": f"{self._post_code}:{self._uprn}"}
        headers = HEADERS.update(
            {
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://report.peterborough.gov.uk",
                "referer": "https://report.peterborough.gov.uk/waste",
            }
        )
        r = s.post(API_URL, headers=headers, data=data)
        r.raise_for_status()

        # website script is sometimes returns a message when it's slow to respond
        if "Loading your bin days..." in r.text:
            print("Loading your bin days...")
            r = s.get(f"{API_URL}/{self._post_code}:{self._uprn}", headers=HEADERS)
            r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")
        wrappers = soup.find_all(
            "div", {"class": "govuk-grid-row waste-service-wrapper"}
        )
        entries = []
        for wrapper in wrappers:
            waste_type = wrapper.find(
                "h3", {"class": "govuk-heading-m waste-service-name"}
            ).text
            rows = wrapper.find_all("div", {"class": "govuk-summary-list__row"})
            for row in rows:
                if "Next collection" in row.text:
                    waste_date = (
                        row.find("dd", {"class": "govuk-summary-list__value"})
                        .text.split(", ")[1]
                        .strip()
                    )
                    # print(waste_type, waste_date)

            entries.append(
                Collection(
                    date=parser.parse(waste_date).date(),
                    t=BIN_MAP.get(waste_type),
                    icon=ICON_MAP.get(BIN_MAP.get(waste_type)),
                )
            )

        sleep(10)
        return entries
