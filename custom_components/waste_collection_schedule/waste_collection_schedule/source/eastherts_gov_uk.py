import json
import logging
import re
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
    "UPRN, POSTCODE & NUMBER": {
        "uprn": "10033104539",
        "address_postcode": "SG9 9AA",
        "address_name_number": "1",
    },
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
    "Paper": "mdi:newspaper",
    "Food": "mdi:food",
}
REGEX = {
    "SID": r"sid=(.+)",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Every UK residential property is allocated a Unique Property Reference Number (UPRN). You can find yours by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "uprn": "Unique Property Reference Number",
    },
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
            "https://eastherts-self.achieveservice.com/service/Bins___When_are_my_Bin_Collection_days",
            headers=HEADERS,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        # get session id
        links = soup.find_all("link", {"href": True})
        for link in links:
            if "apibroker" in link.get("href"):
                sid = re.findall(REGEX["SID"], link.get("href"))[0]
                break

        # now query using the uprn
        timestamp = time.time_ns() // 1_000_000  # epoch time in milliseconds
        payload = {
            "formValues": {"Collection Days": {"inputUPRN": {"value": self._uprn}}}
        }
        scheduleRequest = s.post(
            f"https://eastherts-self.achieveservice.com/apibroker/runLookup?id=683d9ff0e299d&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
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
