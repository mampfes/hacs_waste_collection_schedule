import logging
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from waste_collection_schedule import Collection

TITLE = "Angus Council"
DESCRIPTION = "Source for Angus Council (MyAngus/Granicus)"
URL = "https://www.angus.gov.uk"
TEST_CASES = {
    "Test": {"uprn": "117097214", "postcode": "DD11 2RH"},
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, uprn, postcode):
        self._uprn = str(uprn)
        self._postcode = str(postcode).upper()
        # Create a "search safe" postcode (no spaces, lowercase)
        self._postcode_search = self._postcode.replace(" ", "").lower()

    def fetch(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        })

        # Visit Front Door to get Session ID (SID)
        start_url = "https://myangus.angus.gov.uk/service/Bin_collection_dates_V3"
        r1 = session.get(start_url)
        r1.raise_for_status()

        match = re.search(r'[?&]sid=([a-f0-9]{32})', r1.text)
        if not match:
            raise Exception("Could not find Session ID (sid) on Angus Council page")
        sid = match.group(1)

        # Set Time Cookies (Critical - prevents server defaulting to next year)
        now = datetime.now()
        localtime_str = now.strftime("%Y-%m-%d %H:%M:%S")
        session.cookies.set("localtime", localtime_str, domain="myangus.angus.gov.uk")
        session.cookies.set("fs-timezone", "Europe/London", domain="myangus.angus.gov.uk")

        # Perform Search (Initializes the form)
        api_base = f"https://myangus.angus.gov.uk/apibroker/runLookup?id={{}}&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&sid={sid}"
        
        session.headers.update({
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://myangus.angus.gov.uk",
            "Referer": r1.url,
        })

        url_search = api_base.format("686cdfffd9945")
        payload_search = {
            "formId": "AF-Form-37d4dfe5-4407-4f21-848e-ef456949faf2",
            "processId": "AF-Process-a15a2788-7daa-46f0-96c4-75acb62d4496",
            "stage_id": "AF-Stage-6d652139-a8ac-4e28-97b6-0e02ed369933",
            "stage_name": "Stage 1",
            "formValues": {
                "Section 3": {
                    "search": { "value": self._postcode_search, "value_changed": True },
                    "select_NewAddress": { "value": "" }
                }
            }
        }
        session.post(url_search, json=payload_search)

        # Select Address & Get Data (The Main Event)
        url_select = api_base.format("66587d491feab")
        today_str = now.strftime("%Y-%m-%d")
        
        # We must send 'value_changed': True for dates to force recalculation from TODAY
        payload_select = {
            "formId": "AF-Form-37d4dfe5-4407-4f21-848e-ef456949faf2",
            "processId": "AF-Process-a15a2788-7daa-46f0-96c4-75acb62d4496",
            "stage_id": "AF-Stage-6d652139-a8ac-4e28-97b6-0e02ed369933",
            "stage_name": "Stage 1",
            "formValues": {
                "Section 3": {
                    "select_NewAddress": { "value": self._uprn, "value_changed": True },
                    "search": { "value": self._postcode_search, "value_changed": True },
                    "serviceUPRN": { "value": self._uprn, "value_changed": True },
                    "formatted_search": { "value": self._postcode, "value_changed": True },
                    "chooseADate": { "value": today_str, "value_changed": True },
                    "currentDate": { "value": today_str, "value_changed": True }
                }
            }
        }
        r_select = session.post(url_select, json=payload_select)
        r_select.raise_for_status()
        
        data = r_select.json()
        if data.get("result") == "logout":
            raise Exception("Session Rejected (Logout)")

        # Parse XML Response
        raw_xml = data.get("data", "")
        if "<Rows>" not in raw_xml:
            _LOGGER.warning("No rows found in response data")
            return []

        # Wrap in root to handle fragment and parse
        xml_string = f"<root>{raw_xml}</root>"
        root = ET.fromstring(xml_string)
        rows = root.findall(".//Row")

        entries = []
        for row in rows:
            row_data = {}
            for result in row.findall("result"):
                key = result.get("column")
                val = result.text
                if key:
                    row_data[key] = val
            
            date_str = row_data.get("binDate")
            bin_t = row_data.get("binTypeList")
            
            if date_str and bin_t and "1900" not in date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
                    entries.append(
                        Collection(
                            date=dt,
                            t=bin_t,
                            icon=self.get_icon(bin_t)
                        )
                    )
                except ValueError:
                    continue

        return entries

    def get_icon(self, waste_type):
        waste_type = waste_type.lower()
        if "brown" in waste_type or "food" in waste_type: return "mdi:food-apple"
        if "blue" in waste_type or "paper" in waste_type: return "mdi:newspaper"
        if "purple" in waste_type or "general" in waste_type: return "mdi:trash-can"
        if "grey" in waste_type or "glass" in waste_type or "recycling" in waste_type: return "mdi:glass-fragile"
        if "green" in waste_type or "garden" in waste_type: return "mdi:leaf"
        return "mdi:trash-can"