import json
import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Herts Council"
DESCRIPTION = "Source for www.eastherts.gov.uk services for East Herts Council."
URL = "https://www.eastherts.gov.uk"
TEST_CASES = {
    "Example": {
        "address_postcode": "SG9 9AA",
        "address_name_number": "1",
    },
    "Example No Postcode Space": {
        "address_postcode": "SG99AA",
        "address_name_number": "1",
    },
    "UPRN only": {"uprn": "100080738904"},
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        address_name_numer=None,
        address_name_number=None,
        address_street=None,
        street_town=None,
        address_postcode=None,
        uprn=None,
    ):

        self._address_name_number = (
            address_name_number
            if address_name_number is not None
            else address_name_numer
        )
        self._address_street = address_street
        self._street_town = street_town
        self._address_postcode = address_postcode
        self._uprn = uprn

        if address_name_numer is not None:
            _LOGGER.warning(
                "address_name_numer is deprecated. Use address_name_number instead."
            )
        if address_street is not None:
            _LOGGER.warning(
                "address_street is deprecated. Only address_name_number and address_postcode are required"
            )
        if street_town is not None:
            _LOGGER.warning(
                "street_town is deprecated. Only address_name_number and address_postcode are required"
            )

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

    def resolve_year(self, dt):
        today = datetime.now()
        this_year = today.year
        temp_dt = parse(f"{dt} {this_year}")
        if temp_dt.month == 1 and today.month == 12:
            temp_dt = parse(f"{dt} {this_year + 1}")
        return temp_dt

    def fetch(self):

        s = requests.Session()

        # get a uprn is one has not been provided
        if self._uprn is None:
            self._uprn = self.get_uprn_from_postcode(
                s, self._address_postcode.replace(" ", "")
            )

        # set up session
        r = s.get(
            "https://myaccount.eastherts.gov.uk/apibroker/domain/myaccount.eastherts.gov.uk?_=1749291726954&sid=7f3ebb7cfc44db21b2136e03462dcf5",
            headers=HEADERS,
        )
        r.raise_for_status()

        # get session key
        authRequest = s.get(
            "https://myaccount.eastherts.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fmyaccount.eastherts.gov.uk%252Fen%252FAchieveForms%252F%253Fform_uri%253Dsandbox-publish%253A%252F%252FAF-Process-98782935-6101-4962-9a55-5923e76057b6%252FAF-Stage-dcd0ec18-dfb4-496a-a266-bd8fadaa28a7%252Fdefinition.json%2526redirectlink%253D%25252Fen%2526cancelRedirectLink%253D%25252Fen%2526consentMessage%253Dyes&hostname=myaccount.eastherts.gov.uk&withCredentials=true",
            headers=HEADERS,
        )
        authRequest.raise_for_status()
        authData = authRequest.json()
        sessionKey = authData["auth-session"]

        # now query using the uprn
        timestamp = time.time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {"Collection Days": {"inputUPRN": {"value": self._uprn}}}
        }
        scheduleRequest = s.post(
            f"https://myaccount.eastherts.gov.uk/apibroker/runLookup?id=683d9ff0e299d&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sessionKey}",
            headers=HEADERS,
            json=payload,
        )
        scheduleRequest.raise_for_status()
        rowdata = json.loads(scheduleRequest.content)["integration"]["transformed"][
            "rows_data"
        ]["0"]

        temp_dict: dict = {}
        for item in rowdata:
            if "NextDate" in item:
                if rowdata[item] != "":
                    temp_dict.update(
                        {item.replace("NextDate", ""): self.resolve_year(rowdata[item])}
                    )

        entries = []
        for item in temp_dict:
            if item == "GW":
                title = "Garden Waste"
            else:
                title = item
            entries.append(
                Collection(
                    date=temp_dict[item].date(),
                    t=title,
                    icon=ICON_MAP.get(title),
                )
            )

        return entries
