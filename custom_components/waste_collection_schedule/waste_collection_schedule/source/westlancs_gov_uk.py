import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Lancashire Council"
DESCRIPTION = "Source for West Lancashire Council waste collection schedule."
URL = "https://westlancs.gov.uk"
TEST_CASES = {
    "Test 1": {"postcode": "WN8 9QR", "uprn": "10012340497"},
    "Test 2": {"postcode": "WN8 9DA", "uprn": "10012357342"},
}

ICON_MAP = {
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
}

API_URL = "https://your.westlancs.gov.uk/yourwestlancs.aspx"


class Source:
    def __init__(self, postcode, uprn):
        self._postcode = postcode.strip().replace(" ", "+").upper()
        self._uprn = str(uprn)  # Ensure it's a string for comparison

    def fetch(self):
        session = requests.Session()

        # Step 1: Get the list of addresses for the postcode
        url = f"{API_URL}?address={self._postcode}"

        r = session.get(url)
        r.raise_for_status()

        if "no properties found" in r.text.lower():
            raise Exception(f"No properties found for postcode {self._postcode}")

        soup = BeautifulSoup(r.text, "html.parser")

        # Find the GridView table
        gridview = soup.find("table", {"id": re.compile("GridView")})
        if not gridview:
            raise Exception(f"No address table found for postcode {self._postcode}")

        # Find all rows in the table
        rows = gridview.find_all("tr")

        selected_link = None

        # Check each row for our UPRN
        for row in rows:
            # Get all cells in this row
            cells = row.find_all("td")

            # Check if any cell contains our exact UPRN
            for cell in cells:
                if cell.get_text(strip=True) == self._uprn:
                    # Found our UPRN, get the link from this row
                    link = row.find("a")
                    if link:
                        selected_link = link
                        break

            if selected_link:
                break

        if not selected_link:
            raise Exception(
                f"No address found with UPRN {self._uprn} for postcode {self._postcode}"
            )

        # Parse the __doPostBack parameters
        onclick = selected_link.get("href", "")
        match = re.search(
            r"__doPostBack\s*\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)", onclick
        )
        if not match:
            raise Exception(f"Could not parse address link: {onclick}")

        event_target = match.group(1)
        event_argument = match.group(2)

        # Step 2: Submit the form to get the collection details
        form_data = {
            "__EVENTTARGET": event_target,
            "__EVENTARGUMENT": event_argument,
        }

        # Extract ViewState fields (required by ASP.NET)
        for field in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"]:
            element = soup.find("input", {"name": field})
            if element:
                form_data[field] = element.get("value", "")

        r = session.post(url, data=form_data)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        content = soup.get_text()

        # Parse collection dates
        entries = []

        collection_patterns = [
            ("Refuse", r"Next refuse collection:\s*(\d{2}/\d{2}/\d{4})"),
            ("Recycling", r"Next recycling collection:\s*(\d{2}/\d{2}/\d{4})"),
            ("Garden Waste", r"Next garden waste collection:\s*(\d{2}/\d{2}/\d{4})"),
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
