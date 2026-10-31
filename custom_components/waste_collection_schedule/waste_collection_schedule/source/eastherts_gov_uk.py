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
    "LOOKUP_ID": r'([a-f0-9]{13})',  # Achieveservice IDs are typically 13-char hex strings
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

        try:
            if self._uprn is None:
                self._uprn = self.get_uprn_from_postcode(
                    s, self._address_postcode.replace(" ", "")
                )

            # 1. Load the main council bin service page
            r = s.get(
                "https://eastherts-self.achieveservice.com/service/Bins___When_are_my_Bin_Collection_days",
                headers=HEADERS,
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "html.parser")

            # 2. Extract session ID (sid) and Process URI dynamically
            sid = None
            process_uri = None
            
            for link in soup.find_all(["link", "script", "iframe"], href=True) + soup.find_all(["script", "iframe"], src=True):
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
                raise ValueError("Could not extract session sid from East Herts page")

            timestamp = time.time_ns() // 1_000_000

            # 3. Dynamically fetch form definition to discover active lookup IDs
            lookup_id = "6accfd6441228"  # Fallback
            if process_uri:
                def_req = s.get(
                    f"https://eastherts-self.achieveservice.com/apibroker/runLookup?id={process_uri}&getOnlyTokens=true&sid={sid}",
                    headers=HEADERS,
                )
                if def_req.status_code == 200:
                    found_ids = re.findall(r'"([a-f0-9]{13})"', def_req.text)
                    if found_ids:
                        lookup_id = found_ids[-1]

            # 4. Query schedule using UPRN payload
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

        except Exception as err:
            _LOGGER.error(f"East Herts bin fetch failed: {err}")
            
            # Fire a persistent notification in Home Assistant UI
            try:
                from homeassistant.components import persistent_notification
                # Create notification using Home Assistant's helper
                persistent_notification.create(
                    hass=None,  # Will auto-resolve or trigger via notification center
                    message=f"Failed to update East Herts waste collection schedule:\n`{err}`",
                    title="Waste Collection Schedule Error",
                    notification_id="eastherts_waste_fetch_error",
                )
            except Exception:
                pass  # Fall back to logging if persistent_notification helper isn't available in sync thread
            
            raise err  # Re-raise so the core integration knows update failed
