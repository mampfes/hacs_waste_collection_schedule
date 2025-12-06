from datetime import datetime
import re
import urllib3

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Northumberland County Council"
DESCRIPTION = "Source for Northumberland County Council, UK."
URL = "https://www.northumberland.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "NE19 1AA"},
}
ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
    "Food Waste": "mdi:food-apple",
}

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode of your property (e.g., NE19 1AA)",
    }
}

BASE_URL = "https://bincollection.northumberland.gov.uk"


class Source:
    def __init__(self, postcode: str):
        self._postcode: str = str(postcode).upper()
        self._session: requests.Session = None

    def _setup_session(self) -> requests.Session:
        """Initialize and configure the requests session."""
        session = requests.Session()
        session.headers.update(HEADERS)
        # Suppress SSL warnings for council websites with certificate issues
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return session

    def _make_request(self, url: str, method: str = "GET", data: dict = None) -> requests.Response:
        """Make a request with error handling."""
        try:
            if method.upper() == "POST":
                response = self._session.post(url, data=data, verify=False, timeout=30)
            else:
                response = self._session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed for {url}: {e}")

    def _extract_csrf_token(self, soup: BeautifulSoup) -> str:
        """Extract CSRF token from form."""
        csrf_input = soup.find("input", {"name": "_csrf"})
        if not csrf_input:
            raise Exception("CSRF token not found")
        return csrf_input.get("value")

    def _submit_postcode(self) -> tuple[BeautifulSoup, requests.Response]:
        """Submit the postcode and return the response soup and response object."""
        # Get the postcode entry page
        response = self._make_request(f"{BASE_URL}/postcode")
        soup = BeautifulSoup(response.content, "html.parser")

        # Validate form exists
        form = soup.find("form")
        if not form:
            raise Exception("No form found on the postcode page")

        # Prepare and submit form data
        csrf_token = self._extract_csrf_token(soup)
        form_data = {
            "_csrf": csrf_token,
            "postcode": self._postcode
        }

        response = self._make_request(f"{BASE_URL}/postcode", "POST", form_data)
        return BeautifulSoup(response.content, "html.parser"), response

    def _handle_address_selection(self, soup: BeautifulSoup) -> tuple[BeautifulSoup, requests.Response]:
        """Handle address selection if required."""
        # Find address selection form
        form = soup.find("form")
        if not form:
            raise Exception("Address selection form not found")

        # Get CSRF token and address dropdown
        csrf_token = self._extract_csrf_token(soup)
        address_select = form.find("select", {"name": "address"})
        if not address_select:
            raise Exception("Address selection dropdown not found")

        # Select first valid address
        selected_address = self._get_first_valid_address(address_select)
        if not selected_address:
            raise Exception("No valid address options found")

        # Submit address selection
        form_data = {
            "_csrf": csrf_token,
            "address": selected_address
        }

        response = self._make_request(f"{BASE_URL}/address-select", "POST", form_data)
        return BeautifulSoup(response.content, "html.parser"), response

    def _get_first_valid_address(self, address_select) -> str:
        """Get the first valid address from the dropdown options."""
        options = address_select.find_all("option")
        for option in options:
            value = option.get("value")
            if value and value.strip():
                return value
        return None

    def _parse_collection_table(self, soup: BeautifulSoup) -> list[Collection]:
        """Parse collection data from table format."""
        entries = []
        table_rows = soup.find_all("tr")

        for row in table_rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3:  # Date, Day, Type
                date_text = cells[0].get_text(strip=True)
                type_text = cells[2].get_text(strip=True)

                if self._is_valid_collection_row(date_text, type_text):
                    collection = self._create_collection_from_table_row(date_text, type_text)
                    if collection:
                        entries.append(collection)

        return entries

    def _is_valid_collection_row(self, date_text: str, type_text: str) -> bool:
        """Check if table row contains valid collection data."""
        return (date_text and type_text and
                any(waste in type_text.lower() for waste in ["waste", "recycling", "garden", "food"]))

    def _create_collection_from_table_row(self, date_text: str, type_text: str) -> Collection:
        """Create a Collection object from table row data."""
        date_obj = self._parse_date_with_year_inference(date_text, ["%d %B", "%d %b"])
        if date_obj:
            waste_type = self._normalize_waste_type(type_text)
            return Collection(
                date=date_obj,
                t=waste_type,
                icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
            )
        return None

    def _parse_text_format_collections(self, soup: BeautifulSoup) -> list[Collection]:
        """Parse collection data from text format (fallback method)."""
        entries = []
        all_text = soup.get_text()
        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

        for i, line in enumerate(lines):
            if self._line_contains_waste_type(line):
                collection = self._extract_collection_from_text_lines(lines, i, line)
                if collection:
                    entries.append(collection)

        return entries

    def _line_contains_waste_type(self, line: str) -> bool:
        """Check if line contains waste type keywords."""
        return any(waste in line.lower() for waste in ["recycling", "general"])

    def _extract_collection_from_text_lines(self, lines: list, current_index: int, current_line: str) -> Collection:
        """Extract collection data from text lines around current position."""
        # Check next few lines for date information
        for j in range(1, 4):
            if current_index + j < len(lines):
                next_line = lines[current_index + j]
                date_match = re.search(r'(\w+day)\s+(\d{1,2})\s+(\w+)\s+(\d{4})', next_line)

                if date_match:
                    try:
                        day, date_num, month, year = date_match.groups()
                        date_str = f"{date_num} {month} {year}"
                        date_obj = datetime.strptime(date_str, "%d %B %Y").date()

                        waste_type = self._determine_waste_type_from_line(current_line)
                        return Collection(
                            date=date_obj,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                        )
                    except ValueError:
                        continue
        return None

    def _determine_waste_type_from_line(self, line: str) -> str:
        """Determine waste type from line content."""
        line_lower = line.lower()
        if "recycling" in line_lower:
            return "Recycling"
        elif "garden" in line_lower:
            return "Garden Waste"
        else:
            return "General Waste"

    def _parse_date_with_year_inference(self, date_text: str, formats: list) -> datetime.date:
        """Parse date text with automatic year inference."""
        for fmt in formats:
            try:
                current_year = datetime.now().year
                date_with_year = f"{date_text} {current_year}"
                date_obj = datetime.strptime(date_with_year, f"{fmt} %Y").date()

                # If date is in the past, assume it's next year
                if date_obj < datetime.now().date():
                    date_with_year = f"{date_text} {current_year + 1}"
                    date_obj = datetime.strptime(date_with_year, f"{fmt} %Y").date()
                return date_obj
            except ValueError:
                continue
        return None

    def _normalize_waste_type(self, type_text: str) -> str:
        """Normalize waste type text to standard format."""
        waste_type = type_text.replace(" waste", "").strip()
        if waste_type.lower() == "general":
            return "General Waste"
        elif waste_type.lower() == "recycling":
            return "Recycling"
        return waste_type

    def fetch(self) -> list[Collection]:
        """
        Fetch waste collection schedule for the given postcode.

        Process:
        1. Submit postcode to get address options
        2. Select first available address
        3. Parse collection schedule from calendar page

        Returns:
            List of Collection objects with dates, types, and icons
        """
        self._session = self._setup_session()

        # Step 1: Submit postcode
        soup, response = self._submit_postcode()

        # Step 2: Handle address selection if required
        if "address-select" in response.url:
            soup, response = self._handle_address_selection(soup)

        # Step 3: Verify we reached the calendar page
        if "calendar" not in response.url:
            raise Exception("Did not reach calendar page after form submission")

        # Step 4: Parse collection data
        entries = self._parse_collection_table(soup)

        # Step 5: Fallback to text parsing if table parsing failed
        if not entries:
            entries = self._parse_text_format_collections(soup)

        if not entries:
            raise Exception(f"No collection data found for postcode {self._postcode}. "
                          "The website structure may have changed or the postcode may not be valid.")

        return entries