import logging
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Kirklees Council"
DESCRIPTION = "Source for waste collections for Kirklees Council"
URL = "https://www.kirklees.gov.uk"
TEST_CASES = {
    "Test_001": {"door_num": 20, "postcode": "HD9 6LW"},
    "test_002": {"door_num": "6", "postcode": "hd9 1js"},
}

BASE_URL = "https://www.kirklees.gov.uk/beta/your-property-bins-recycling/your-bins/"

PARAMS = {
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "__LASTFOCUS": "",
    "__VIEWSTATE": "",
    "__VIEWSTATEGENERATOR": "",
    "__SCROLLPOSITIONX": "0",
    "__SCROLLPOSITIONY": "0",
    "__EVENTVALIDATION": "",
    "ctl00$ctl00$cphPageBody$cphContent$hdnBinUPRN": "",
    "ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$txtGeoPremises": "",
    "ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$txtGeoSearch": "",
    "ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$butGeoSearch": ""
}

COLLECTION_REGEX = "(Recycling|Domestic|Garden Waste).*collection date ([0-3][0-9] [a-zA-Z]* [0-9]{4})"

ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN WASTE": "mdi:leaf",
}


class Source:
    def __init__(self, door_num, postcode):
        self._door_num = door_num
        self._postcode = postcode
        self._session = requests.Session()

    def fetch(self):
        entries = []
        self._session.cookies.set("cookiesacceptedGDPR", "true", domain=".kirklees.gov.uk")

        r0 = self._session.get(f"{BASE_URL}/default.aspx")
        r0.raise_for_status()
        r0_bs4 = BeautifulSoup(r0.text, features="html.parser")
        PARAMS['__VIEWSTATE'] = r0_bs4.find("input", {"id": "__VIEWSTATE"})['value']
        PARAMS['__VIEWSTATEGENERATOR'] = r0_bs4.find("input", {"id": "__VIEWSTATEGENERATOR"})['value']
        PARAMS['__EVENTVALIDATION'] = r0_bs4.find("input", {"id": "__EVENTVALIDATION"})['value']

        PARAMS['ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$txtGeoPremises'] = self._door_num
        PARAMS['ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$txtGeoSearch'] = self._postcode
        PARAMS['ctl00$ctl00$cphPageBody$cphContent$thisGeoSearch$butGeoSearch'] = r0_bs4.find("input", {"id": "butGeoSearch"})['value']

        r1 = self._session.get(f"{BASE_URL}/default.aspx", params=PARAMS)
        r1.raise_for_status()
        r1_bs4 = BeautifulSoup(r1.text, features="html.parser")
        cal_link = r1_bs4.find("a", {"id": "cphPageBody_cphContent_wtcDomestic240__LnkCalendar"})['href']

        r2 = self._session.get(f"{BASE_URL}/{cal_link}")
        r2.raise_for_status()
        r2_bs4 = BeautifulSoup(r2.text, features="html.parser")

        for collection in r2_bs4.find_all("img", {"id": re.compile('^cphPageBody_cphContent_rptr_Sticker_rptr_Collections_[0-9]_rptr_Bins_[0-9]_img_binType_[0-9]')}):
            matches = re.findall(COLLECTION_REGEX, collection['alt'])
            entries.append(
                Collection(
                    date=datetime.strptime(matches[0][1], "%d %B %Y").date(),
                    t=matches[0][0],
                    icon=ICON_MAP.get(matches[0][0].upper()),
                )
            )
        return entries
