from datetime import datetime, date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Kiama City Council"
DESCRIPTION = "Source script for kiama.nsw.gov.au"
URL = "https://kiama.nsw.gov.au"
COUNTRY = "au"
TEST_CASES = {"TestName1": {"geolocationid": "38da9173-322a-43fd-953b-3b51803dbe94"}, "TestName2": {"geolocationid": "f2c04fcf-e3d3-424e-aa90-1d365bbf0130"}}

API_URL = "https://www.kiama.nsw.gov.au/ocapi/Public/myarea/wasteservices"

ICON_MAP = {
    "Urban garbage": "mdi:trash-can",
    "Urban food & garden organics": "mdi:leaf",
    "Urban recycling": "mdi:recycle",
}



def parse_date(date_str):
    """Convert date string like 'Fri 20/6/2025' to ISO format '2025-06-20'."""
    try:
        # Parse date string (format: 'Fri DD/M/YYYY')
        return datetime.strptime(date_str, "%a %d/%m/%Y").date()
    except ValueError as e:
        return f"Invalid date format: {date_str}"


class Source:
    def __init__(self, geolocationid):
        self._geolocationid = geolocationid

    def fetch(self):
        data = {"Referer": "https://www.kiama.nsw.gov.au/Services/Waste-and-recycling/Find-my-bin-collection-dates"}

        pageurl = f"https://www.kiama.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={self._geolocationid}&ocsvclang=en-AU"
        response = requests.get(f"{pageurl}", data=data)
        response.raise_for_status()
            # Parse JSON to get HTML content
        data = response.json()
        if not data.get("success") or "responseContent" not in data:
            raise ValueError("Invalid JSON response structure")

        html_content = data["responseContent"]

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all waste service result articles
        results = soup.find_all("div", class_="waste-services-result")
        entries = []
        if results:
            for result in results:
                # Get bin type from <h3>
                bin_type = result.find("h3")
                bin_type = bin_type.get_text(strip=True) if bin_type else "Unknown"

                # Get next service date from <div class="next-service">
                next_service = result.find("div", class_="next-service")
                day = next_service.get_text(strip=True) if next_service else "No date provided"

                # Only print if a date is available
                if day and day != "":
                    entries.append(
                        Collection(
                            date=parse_date(day),
                            t=bin_type,
                            icon=ICON_MAP.get(bin_type),
                        )
                    )
        return entries
