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
       "url": "https://www.southoxon.gov.uk/"
    },
    {
       "title": "Vale of White Horse District Council",
       "url": "https://www.whitehorsedc.gov.uk/"
    },
]
DESCRIPTION = (
    """Consolidated source for waste collection services from:
        South Oxfordshire District Council
        Vale of White Horse District Council
        """
)
TEST_CASES = {
    "VOWH" : {"uprn": "100120903018"},
    "SO" : {"uprn": "100120883950"},
}

ICON_MAP = {
    "GREY BIN": "mdi:trash-can",
    "GREEN BIN": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
    "SMALL ELECTRICAL ITEMS": "mdi:hair-dryer",
    "FOOD BIN": "mdi:food-apple",
    "TEXTILES": "mdi:hanger"
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = uprn

    def fetch(self):

        s = requests.Session()

        # Used https://github.com/robbrad/UKBinCollectionData/blob/master/uk_bin_collection/uk_bin_collection/councils/SouthOxfordshireCouncil.py
        # as a reference. This works for both councils, using the same url.
        # UPRN is passed in via a cookie. Set cookies/params and GET the page
        cookies = {
            'SVBINZONE':  f'SOUTH%3AUPRN%40{self._uprn}',
        }
        headers = {
            'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language':           'en-GB,en;q=0.7',
            'Cache-Control':             'max-age=0',
            'Connection':                'keep-alive',
            'Referer':                   'https://eform.southoxon.gov.uk/ebase/BINZONE_DESKTOP.eb?SOVA_TAG=SOUTH&ebd=0&ebz=1_1668467255368',
            'Sec-Fetch-Dest':            'document',
            'Sec-Fetch-Mode':            'navigate',
            'Sec-Fetch-Site':            'same-origin',
            'Sec-Fetch-User':            '?1',
            'Sec-GPC':                   '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent':                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }
        params = {
            'SOVA_TAG': 'SOUTH',
            'ebd':      '0',
        }

        if self._uprn:
            # GET request returns schedule for matching uprn
            r = s.get('https://eform.southoxon.gov.uk/ebase/BINZONE_DESKTOP.eb', params=params,
                                headers=headers, cookies=cookies)
            responseContent = r.text

        else:
            raise Exception("Address not found")        

        entries = []

        # Extract waste types and dates from responseContent
        soup = BeautifulSoup(responseContent, "html.parser")
        soup.prettify()

        for bin in soup.find_all("div", {"class": "binextra"}):
            bin_info = bin.text.split("-")
            try:
                # No date validation since year isn't included on webpage
                bin_date = bin_info[0].strip()
                bin_type = bin_info[1].strip()
            except Exception as ex:
                raise ValueError(f"Error parsing bin data: {ex}")

            for round_type in ICON_MAP:
                if round_type in bin_type.upper():
                    entries.append(
                        Collection(
                            date = parse(bin_date).date(),
                            t = round_type,
                            icon = ICON_MAP.get(round_type)
                        )
                    )

        return entries
