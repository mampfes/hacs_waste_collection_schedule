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
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}
BIN_MAP = {
    "Black Bin": "Empty Bin 240L Black",
    "Green Bin": "Empty Bin 240L Green",
    "Brown Bin": "Empty Bin 240L Brown",
}  # map new bin names to old bin names for compatibility

PARAM_TRANSLATIONS = {
    "en": {
        "name": "Not Used",
        "number": "Not Used",  # no longer used, but retained for config compatibility
        "post_code": "Postcode",
        "uprn": "UPRN",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "name": "Leave empty it will not be used anywhere and is just for compatibility with old configurations.",
        "number": "Leave empty it will not be used anywhere and is just for compatibility with old configurations.",
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
    }
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, post_code=None, number=None, name=None, uprn=None):
        self._post_code = post_code
        self._number = (
            number  # no longer required, but retained for config compatibility
        )
        self._name = name  # no longer required, but retained for config compatibility
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

    def get_schedule(self, s, p, u):
        # website returns "loading" page when it's running slow, so retries may be necessary
        # website limits number of searches per day and returns 403 error when exceeded
        retries = 5
        p = p.replace(" ", "%20")  # URL-encode space in postcode
        url = f"{API_URL}/{p}:{u}"  
        headers = HEADERS.copy()
        headers.update({
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "en-GB,en;q=0.5",
            "referer": "https://report.peterborough.gov.uk/waste",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1"
        })
        _LOGGER.debug(f"Sending GET to {url} with headers={headers}")
        for attempt in range(retries):
            try:
                r = s.get(url, headers=headers)
                _LOGGER.debug(f"Attempt {attempt}: Status {r.status_code}, Response: {r.text[:200]}")
                r.raise_for_status()
                # check "loading" page hasn't been returned
                if "loading" not in r.text.lower():
                    return r.text
                else:
                    _LOGGER.warning(
                        f"Schedule retrieval attempt {attempt} failed. Retrying..."
                    )
            except requests.RequestException as e:
                _LOGGER.warning(f"Request {attempt} failed: {e}")
            sleep(5)
        _LOGGER.error(f"Failed to retrieve schedule for {p}:{u} after {retries} attempts")
        return None

    def fetch(self):
        s = requests.Session()

        # legacy configs may be missing some details so try and populate them
        if self._uprn is None:
            self._uprn = self.get_uprn_from_postcode(s, self._post_code)
        if self._post_code is None:
            self._post_code = self.get_postcode_from_uprn(s, self._uprn)
        self._post_code = str(self._post_code.replace(" ", ""))

        # visit page to get session cookies
        r = s.get(API_URL, headers=HEADERS)
        r.raise_for_status()

        # get schedule
        schedule = self.get_schedule(s, self._post_code, self._uprn)
        if schedule is None:
            _LOGGER.error(f"No schedule data retrieved for postcode {self._post_code}, UPRN {self._uprn}")
            return []  # Return empty list to avoid crashing HA
        soup = BeautifulSoup(schedule, "html.parser")
        wrappers = soup.find_all(
            "div", {"class": "govuk-grid-row waste-service-wrapper"}
        )
        entries = []
        for wrapper in wrappers:
            waste_type = wrapper.find(
                "h3", {"class": "govuk-heading-m waste-service-name"}
            )
            if not waste_type:
                _LOGGER.warning(f"No waste type found in wrapper: {wrapper}")
                continue
            waste_type = waste_type.text
            rows = wrapper.find_all("div", {"class": "govuk-summary-list__row"})
            for row in rows:
                if "Next collection" in row.text:
                    waste_date = (
                        row.find("dd", {"class": "govuk-summary-list__value"})
                        .text.split(", ")[1]
                        .strip()
                    )
                    entries.append(
                        Collection(
                            date=parser.parse(waste_date).date(),
                            t=BIN_MAP.get(waste_type, waste_type),
                            icon=ICON_MAP.get(BIN_MAP.get(waste_type, waste_type)),
                        )
                    )
        return entries
