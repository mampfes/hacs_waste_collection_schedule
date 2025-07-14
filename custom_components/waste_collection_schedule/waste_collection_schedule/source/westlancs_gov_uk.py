import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Lancashire Council"
DESCRIPTION = "Source for West Lancashire Council waste collection schedule."
URL = "https://westlancs.gov.uk"
TEST_CASES = {
    "Test 1": {"postcode": "WN8 9QR"},
    "Test 2": {"postcode": "L40 1SB"},
}

ICON_MAP = {
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
}

API_URL = "https://your.westlancs.gov.uk/yourwestlancs.aspx"


class Source:
    def __init__(self, postcode):
        self._postcode = postcode.strip().replace(" ", "+").upper()

    def fetch(self):
        # Step 1: Get the list of addresses for the postcode
        session = requests.Session()
        
        url = f"{API_URL}?address={self._postcode}"
        
        r = session.get(url)
        r.raise_for_status()
        
        if "no properties found" in r.text.lower():
            raise Exception(f"No properties found for postcode {self._postcode}")
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Find all links that contain __doPostBack
        all_links = soup.find_all("a")
        address_links = []
        
        for link in all_links:
            href = link.get("href", "")
            if "__doPostBack" in href and "GridView" in href:
                address_links.append(link)
        
        if not address_links:
            # Fallback: try to find any doPostBack links
            for link in all_links:
                href = link.get("href", "")
                if "__doPostBack" in href:
                    address_links.append(link)
        
        if not address_links:
            raise Exception(f"No address links found for postcode {self._postcode}")
        
        # Get the first address link
        first_link = address_links[0]
        onclick = first_link.get("href", "")
        
        # Parse the __doPostBack parameters
        match = re.search(r"__doPostBack\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)", onclick)
        if not match:
            raise Exception(f"Could not parse address link: {onclick}")
        
        event_target = match.group(1)
        event_argument = match.group(2)
        
        # Get form data for postback
        form_data = {
            "__EVENTTARGET": event_target,
            "__EVENTARGUMENT": event_argument,
        }
        
        # Extract ViewState and other ASP.NET form fields
        for field in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION", "__VIEWSTATEENCRYPTED"]:
            element = soup.find("input", {"name": field})
            if element:
                form_data[field] = element.get("value", "")
        
        # Step 2: Submit the form to get the collection details
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": url,
            "Origin": "https://your.westlancs.gov.uk"
        }
        
        r = session.post(url, data=form_data, headers=headers)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.get_text()
        
        entries = []
        
        # Look for collection information
        collection_patterns = [
            ("Refuse", r"Next refuse collection:\s*(\d{2}/\d{2}/\d{4})"),
            ("Recycling", r"Next recycling collection:\s*(\d{2}/\d{2}/\d{4})"),
            ("Garden Waste", r"Next garden waste collection:\s*(\d{2}/\d{2}/\d{4})")
        ]
        
        for waste_type, pattern in collection_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            
            if match:
                date_str = match.group(1)
                try:
                    date = datetime.strptime(date_str, "%d/%m/%Y").date()
                    entries.append(
                        Collection(
                            date=date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type.lower().split()[0]),
                        )
                    )
                except ValueError:
                    pass
            elif waste_type == "Garden Waste" and "Not subscribed" in content:
                # Skip garden waste if not subscribed
                continue
        
        if not entries:
            raise Exception("No collection dates found")
        
        return entries