import json
import logging
import re
from datetime import datetime
import requests
from waste_collection_schedule import Collection

TITLE = "Scottish Borders Council"
DESCRIPTION = "Source for Scottish Borders Council (Bartec Municipal)"
URL = "https://scotborders-live-portal.bartecmunicipal.com/Embeddable/CollectionCalendar"
TEST_CASES = {
    "Test": {"uprn": "116073632", "postcode": "TD9 9HL"} 
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, uprn, postcode):
        self._uprn = str(uprn)
        self._postcode = postcode

    def fetch(self):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": URL,
            "Origin": "https://scotborders-live-portal.bartecmunicipal.com"
        })

        # GET page for Token
        r1 = session.get(URL)
        r1.raise_for_status()
        token = self._get_token(r1.text)

        # Search Postcode
        r2 = session.post(f"{URL}?handler=SearchPostcode", data={
            "__RequestVerificationToken": token,
            "SelectedPostcode": self._postcode
        })
        r2.raise_for_status()
        token = self._get_token(r2.text)

        # Select UPRN
        r3 = session.post(f"{URL}?handler=SelectPrem", data={
            "__RequestVerificationToken": token,
            "SelectedPostcode": self._postcode,
            "SelectedPremises": self._uprn
        })
        r3.raise_for_status()

        # Extract Data
        pattern = re.compile(r'dataSource":\s*ejs\.data\.DataUtil\.parse\.isJson\(\s*(\[.*?\])\s*\)', re.DOTALL)
        matches = pattern.findall(r3.text)

        if not matches:
            raise Exception("No JSON data blocks found in page source.")

        entries = []
        found_valid_block = False

        for json_str in matches:
            try:
                data = json.loads(json_str)
                # Filter out empty lists or the address list (which has no 'Subject')
                if not isinstance(data, list) or not data:
                    continue
                
                if "Subject" not in data[0]:
                    continue

                # Found the schedule block!
                found_valid_block = True
                
                for item in data:
                    subject = item.get("Subject")
                    date_str = item.get("StartTime")
                    
                    if not subject or not date_str: continue

                    # Parse date "2025-12-16T00:00:00"
                    try:
                        dt = datetime.fromisoformat(date_str).date()
                    except ValueError:
                        dt = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()
                    
                    entries.append(
                        Collection(
                            date=dt,
                            t=subject,
                            icon=self.get_icon(subject)
                        )
                    )
                break # Stop looking after finding the right block

            except json.JSONDecodeError:
                continue

        if not found_valid_block:
             raise Exception("Found JSON blocks, but none contained bin schedule data.")

        return entries

    def _get_token(self, html):
        match = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', html)
        if match: return match.group(1)
        match = re.search(r"name='__RequestVerificationToken' type='hidden' value='([^']+)'", html)
        if match: return match.group(1)
        raise Exception("Could not find Verification Token.")

    def get_icon(self, waste_type):
        waste_type = waste_type.lower()
        if "food" in waste_type: return "mdi:food-apple"
        if "recycle" in waste_type or "recycling" in waste_type: return "mdi:recycle"
        if "garden" in waste_type: return "mdi:leaf"
        return "mdi:trash-can"
