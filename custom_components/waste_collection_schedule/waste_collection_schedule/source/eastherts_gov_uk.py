import json
import logging
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

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
    "Refuse": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Waste": Icons.GARDEN,
    "Paper": Icons.PAPER,
    "Food": Icons.BIO_KITCHEN,
}
REGEX = {
    "SID": r"sid=(.+)",
    "PROCESS_URI": r"(AF-Process-[a-f0-9-]+)",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Every UK residential property is allocated a Unique Property Reference Number (UPRN). You can find yours by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
    },
}

PARAM_TRANSLATIONS = {
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

    def get_uprn_from_postcode(self, s, pcode):
        r = s.get(f"https://uprn.uk/postcode/{pcode}")
        soup = BeautifulSoup(r.content, "html.parser")
        cols = soup.find("div", {"class": "threecol"})
        li = cols.find("li")
        pcode_uprn = li.find("a", href=True).text
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

        if self._uprn is None:
            self._uprn = self.get_uprn_from_postcode(
                s, self._address_postcode.replace(" ", "")
            )

        # 1. Load the main bin collection service page
        r = s.get(
            "https://eastherts-self.achieveservice.com/service/Bins___When_are_my_Bin_Collection_days",
            headers=HEADERS,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # 2. Dynamically extract session ID (sid) and Process URI
        sid = None
        process_uri = None

        for link in soup.find_all(
            ["link", "script", "iframe"], href=True
        ) + soup.find_all(["script", "iframe"], src=True):
            val = link.get("href") or link.get("src")
            if "apibroker" in val and not sid:
                sid_match = re.findall(REGEX["SID"], val)
                if sid_match:
                    sid = sid_match[0]
            if "AF-Process-" in val and not process_uri:
                process_match = re.findall(REGEX["PROCESS_URI"], val)
                if process_match:
                    process_uri = process_match[0]

        if not sid or not process_uri:
            text_match_sid = re.search(r"sid=([a-f0-9]{32})", r.text)
            if text_match_sid and not sid:
                sid = text_match_sid.group(1)
            text_match_process = re.search(r"(AF-Process-[a-f0-9-]+)", r.text)
            if text_match_process and not process_uri:
                process_uri = text_match_process.group(1)

        if not sid:
            raise ValueError("Could not extract sid token from East Herts page")

        timestamp = time.time_ns() // 1_000_000

        # 3. Resolve dynamic lookup package ID
        lookup_id = "6accfd6441228"  # Known active fallback
        if process_uri:
            try:
                def_req = s.get(
                    f"https://eastherts-self.achieveservice.com/apibroker/runLookup?id={process_uri}&getOnlyTokens=true&sid={sid}",
                    headers=HEADERS,
                )
                if def_req.status_code == 200:
                    found_ids = re.findall(r'"([a-f0-9]{13})"', def_req.text)
                    if found_ids:
                        lookup_id = found_ids[-1]
            except Exception as err:
                _LOGGER.debug(
                    "Dynamic lookup extraction issue, using fallback: %s", err
                )

        # 4. Fetch waste collection schedule
        payload = {
            "formValues": {"Collection Days": {"inputUPRN": {"value": self._uprn}}}
        }
        scheduleRequest = s.post(
            f"https://eastherts-self.achieveservice.com/apibroker/runLookup?id={lookup_id}&repeat_against=&noRetry=true&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
            headers=HEADERS,
            json=payload,
        )
        scheduleRequest.raise_for_status()
        rowdata = json.loads(scheduleRequest.content)["integration"]["transformed"][
            "rows_data"
        ]["0"]

        # 5. Extract NextDate entries
        bin_names = {
            "Refuse": "Refuse",
            "Recycling": "Recycling",
            "GW": "Garden Waste",
            "Paper": "Paper",
            "Food": "Food",
        }

        entries = []
        seen_combos = set()

        for key, val in rowdata.items():
            if not val or val == "":
                continue

            if "NextDate" in key:
                clean_type = key.replace("NextDateRaw", "").replace("NextDate", "")
                title = bin_names.get(clean_type, clean_type)

                try:
                    if "Raw" in key:
                        collection_date = parse(val).date()
                    else:
                        collection_date = self.resolve_year(val).date()

                    combo_key = (title, collection_date)
                    if combo_key not in seen_combos:
                        seen_combos.add(combo_key)
                        entries.append(
                            Collection(
                                date=collection_date,
                                t=title,
                                icon=ICON_MAP.get(title),
                            )
                        )
                except Exception as parse_err:
                    _LOGGER.debug(
                        "Failed to parse date for {key} ('{val}'): {parse_err}"
                    )

        return entries
        
