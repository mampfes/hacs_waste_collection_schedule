from datetime import datetime

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


class Source:
    def __init__(self, postcode: str):
        self._postcode: str = str(postcode).upper()

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        s.headers.update(HEADERS)

        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Access the postcode entry page
        try:
            r = s.get(
                "https://bincollection.northumberland.gov.uk/postcode",
                verify=False,
                timeout=30
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to access Northumberland bin collection service: {e}")

        soup = BeautifulSoup(r.content, "html.parser")

        # Find the form with CSRF token and postcode field
        form = soup.find("form")
        if not form:
            raise Exception("No form found on the postcode page")

        # Get CSRF token
        csrf_input = form.find("input", {"name": "_csrf"})
        if not csrf_input:
            raise Exception("CSRF token not found")

        csrf_token = csrf_input.get("value")

        # Prepare form data
        form_data = {
            "_csrf": csrf_token,
            "postcode": self._postcode
        }

        # Submit the postcode form
        try:
            r = s.post(
                "https://bincollection.northumberland.gov.uk/postcode",
                data=form_data,
                verify=False,
                timeout=30
            )
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to submit postcode form: {e}")

        # Check if we got redirected to address selection
        soup = BeautifulSoup(r.content, "html.parser")

        if "address-select" in r.url:
            # We need to select an address from the dropdown
            form = soup.find("form")
            if not form:
                raise Exception("Address selection form not found")

            # Get CSRF token
            csrf_input = form.find("input", {"name": "_csrf"})
            if not csrf_input:
                raise Exception("CSRF token not found in address selection form")

            csrf_token = csrf_input.get("value")

            # Find the address select dropdown
            address_select = form.find("select", {"name": "address"})
            if not address_select:
                raise Exception("Address selection dropdown not found")

            # Get the first address option (skip empty options)
            options = address_select.find_all("option")
            selected_address = None
            for option in options:
                if option.get("value") and option.get("value").strip():
                    selected_address = option.get("value")
                    break

            if not selected_address:
                raise Exception("No valid address options found")

            # Submit the address selection form
            form_data = {
                "_csrf": csrf_token,
                "address": selected_address
            }

            try:
                r = s.post(
                    "https://bincollection.northumberland.gov.uk/address-select",
                    data=form_data,
                    verify=False,
                    timeout=30
                )
                r.raise_for_status()
            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to submit address selection: {e}")

            soup = BeautifulSoup(r.content, "html.parser")

        # Now we should be on the calendar page with collection data
        if "calendar" not in r.url:
            raise Exception("Did not reach the calendar page after address selection")

        entries = []

        # Parse the collection schedule from the calendar page
        # Look for table rows with collection data
        table_rows = soup.find_all("tr")
        for row in table_rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 3:  # Date, Day, Type
                date_cell = cells[0].get_text(strip=True)
                day_cell = cells[1].get_text(strip=True)
                type_cell = cells[2].get_text(strip=True)

                # Try to parse the date
                if date_cell and type_cell and any(waste in type_cell.lower() for waste in ["waste", "recycling", "garden", "food"]):
                    try:
                        # Try different date formats
                        date_obj = None
                        for fmt in ["%d %B", "%d %b"]:
                            try:
                                # Add current year for parsing
                                current_year = datetime.now().year
                                date_with_year = f"{date_cell} {current_year}"
                                date_obj = datetime.strptime(date_with_year, f"{fmt} %Y").date()

                                # If the date is in the past, assume it's next year
                                if date_obj < datetime.now().date():
                                    date_with_year = f"{date_cell} {current_year + 1}"
                                    date_obj = datetime.strptime(date_with_year, f"{fmt} %Y").date()
                                break
                            except ValueError:
                                continue

                        if date_obj:
                            # Clean up the waste type
                            waste_type = type_cell.replace(" waste", "").strip()
                            if waste_type.lower() == "general":
                                waste_type = "General Waste"
                            elif waste_type.lower() == "recycling":
                                waste_type = "Recycling"

                            entries.append(
                                Collection(
                                    date=date_obj,
                                    t=waste_type,
                                    icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                                )
                            )
                    except ValueError:
                        continue

        # Also look for the "next collection days" section which might have different formatting
        if not entries:
            # Look for specific divs or sections containing collection info
            all_text = soup.get_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]

            import re
            for i, line in enumerate(lines):
                # Look for lines with waste types followed by date info
                if any(waste in line.lower() for waste in ["recycling", "general"]):
                    # Check next few lines for date information
                    for j in range(1, 4):  # Check next 3 lines
                        if i + j < len(lines):
                            next_line = lines[i + j]
                            # Look for date patterns like "Monday 29 September 2025"
                            date_match = re.search(r'(\w+day)\s+(\d{1,2})\s+(\w+)\s+(\d{4})', next_line)
                            if date_match:
                                try:
                                    day, date_num, month, year = date_match.groups()
                                    date_str = f"{date_num} {month} {year}"
                                    date_obj = datetime.strptime(date_str, "%d %B %Y").date()

                                    waste_type = "General Waste"
                                    if "recycling" in line.lower():
                                        waste_type = "Recycling"
                                    elif "garden" in line.lower():
                                        waste_type = "Garden Waste"

                                    entries.append(
                                        Collection(
                                            date=date_obj,
                                            t=waste_type,
                                            icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                                        )
                                    )
                                except ValueError:
                                    continue

        if not entries:
            raise Exception(f"No collection data found for postcode {self._postcode}. The website structure may have changed or the postcode may not be valid.")

        return entries