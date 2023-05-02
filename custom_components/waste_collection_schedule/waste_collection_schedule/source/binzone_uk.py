import logging

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection

TITLE = "Binzone"
URL = "https://www.southoxon.gov.uk/"
EXTRA_INFO = [
    {
        "title": "South Oxfordshire District Council",
        "url": "https://www.southoxon.gov.uk/",
    },
    {
        "title": "Vale of White Horse District Council",
        "url": "https://www.whitehorsedc.gov.uk/",
    },
]
DESCRIPTION = """Consolidated source for waste collection services from:
        South Oxfordshire District Council
        Vale of White Horse District Council
        """
TEST_CASES = {
    "VOWH": {"uprn": "100120903018"},
    "SO": {"uprn": "100120883950"},
}

ICON_MAP = {
    "GREY BIN": "mdi:trash-can",
    "GREEN BIN": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
    "SMALL ELECTRICAL ITEMS": "mdi:hair-dryer",
    "FOOD BIN": "mdi:food-apple",
    "TEXTILES": "mdi:hanger",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):

        s = requests.Session()

        # Used https://github.com/robbrad/UKBinCollectionData/blob/master/uk_bin_collection/uk_bin_collection/councils/SouthOxfordshireCouncil.py
        # as a reference. This works for both councils, using the same url.
        # UPRN is passed in via a cookie. Set cookies/params and GET the page
        cookies = {
            "SVBINZONE": f"SOUTH%3AUPRN%40{self._uprn}",
        }

        params = {
            "SOVA_TAG": "SOUTH",
            "ebd": "0",
        }

        # GET request returns schedule for matching uprn
        r = s.get(
            "https://eform.southoxon.gov.uk/ebase/BINZONE_DESKTOP.eb",
            params=params,
            cookies=cookies,
        )
        r.raise_for_status()
        responseContent = r.text

        entries = []

        # Extract waste types and dates from responseContent
        soup = BeautifulSoup(responseContent, "html.parser")
        soup.prettify()

        for bin in soup.find_all("div", {"class": "binextra"}):
            bin_info = bin.text.split("-")
            try:
                # No date validation since year isn't included on webpage
                bin_date = bin_info[0].strip().replace("Your usual collection day is different this week", "")
                bin_type = bin_info[1].strip()
            except Exception as ex:
                raise ValueError(f"Error parsing bin data: {ex}")

            for round_type in ICON_MAP:
                if round_type in bin_type.upper():
                    entries.append(
                        Collection(
                            date=parse(bin_date).date(),
                            t=round_type,
                            icon=ICON_MAP.get(round_type),
                        )
                    )

        return entries
