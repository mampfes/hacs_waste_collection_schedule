from __future__ import annotations

import datetime as dt
from waste_collection_schedule import Collection
from typing import Any, Dict, List
import re
import requests
from bs4 import BeautifulSoup

# Metadata used by the Waste Collection Schedule integration
TITLE = "Norwich City Council"
DESCRIPTION = "Source for Norwich City Council bin collection via Whitespace BNR platform"
URL = "https://www.norwich.gov.uk/bins-and-recycling"

API_URL = "https://bnr-wrp.whitespacews.com"

# Test cases used by the integration framework for validation
TEST_CASES = { 
    "GoodExample":
        {
            "property_name_or_number": "33",
            "street_name":             "Carrow Road",
            "postcode":                "NR1 1HS"
        },
    "FlatAddress":
        {
            "property_name_or_number": "Flat 1",
            "street_name":             "Unthank Road",
            "postcode":                "NR2 2RN"
        },
    "UncompletedRoadName":
        {
            "property_name_or_number": "18",
            "street_name":             "Aylsham",
            "postcode":                "NR3 3HG"
        },
    "PostcodeMissingSpace":
        {
            "property_name_or_number": "258",
            "street_name":             "North Park Avenue",
            "postcode":                "NR47ED"
        },
}

# Mapping of service names (as they appear on the website)
# to the internal representation used by the integration
COLLECTION_TYPES = {
    "Domestic Waste Collection Service": {
        "title": "Domestic Waste",
        "icon": "mdi:trash-can",
        "alias": "Black Bin",
    },
    "Food Waste Collection Service": {
        "title": "Food Waste",
        "icon": "mdi:food-apple",
        "alias": "Food Bin",
    },
    "Recycling Collection Service": {
        "title": "Recycling",
        "icon": "mdi:recycle",
        "alias": "Blue Bin",
    },
    "Garden Waste Collection Service": {
        "title": "Garden Waste",
        "icon": "mdi:leaf",
        "alias": "Brown Bin",
    },
}


class Source:
    """
    Scraper for Norwich City Council's Whitespace BNR waste collection system.
    """

    def __init__(
        self,
        property_name_or_number: str,
        street_name: str,
        postcode: str,
    ):
        """
        Parameters:
        There must be at least 5 characters across the fields in order to continue
        - property_name_or_number: Name or number of the property
        - street_name: Street name of the property
        - postcode: Postcode of the property
        """
        self._property_name_or_number = property_name_or_number
        self._street_name = street_name
        self._postcode = postcode

        self._headers = {
            "User-Agent": "Mozilla/5.0 (HomeAssistant WasteCollectionSchedule)",
            "Accept": "application/json,text/javascript,*/*;q=0.01",
        }


    def fetch(self) -> List[Collection]:
        """
        Main entry point: orchestrates the crawl.
        Returns a list of Collection objects sorted by date.
        """

        session = requests.Session()

        # Step 1: Load the main page and extract the tracking link
        tracking = self._begin_crawl(session, self._headers)

        if not tracking:
            raise ValueError("NCC Your Bins website is not accessible.")

        # Step 2: Submit the address search form and get the selected address link
        schedule = self._compose_search_query(session, self._headers, tracking)

        if not schedule:
            raise ValueError("No matching address found for the provided details")

        # Step 3: Fetch the actual collection schedule
        entries = self._get_collections(session, self._headers, schedule)

        if not entries:
            raise ValueError("No collection data returned for the selected address")

        # Ensure chronological order
        entries.sort(key=lambda item: item.date)

        return entries


    def _begin_crawl(self, session: requests.Session, headers: Dict[str, str]) -> Any:
        """
        Initiates the crawl by accessing the main page and retrieving the necessary session data.
        """
        resp = requests.get(API_URL)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the the link to check your bin day.
        link = soup.find("a", string="View my collections")

        return link.get("href") if link else None


    def _compose_search_query(self, session: requests.Session, headers: Dict[str, str], tracking: str) -> Any:
        """
        Loads the Whitespace search form, fills it with the user’s address,
        submits it, and extracts the link to the specific property.
        """

        # Load the form page
        resp = requests.get(tracking)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract form metadata
        form = soup.find("form")
        action = form.get("action")
        method = form.get("method", "get").lower()

        # Collect the form fields
        data = {}
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                data[name] = value

        # Insert the user-supplied address fields
        data["address_name_number"] = self._property_name_or_number
        data["address_street"] = self._street_name
        data["address_postcode"] = self._postcode

        # Submit the form using the correct HTTP method
        if method == "post":
            form = session.post(action, headers=headers, data=data)
        else:
            form = session.get(action, headers=headers, params=data)

        # Parse the results page
        fresh_soup = BeautifulSoup(form.text, "html.parser")
        address_links = fresh_soup.find_all("a")

        # Identify the correct address by matching both number/name and street
        required_words = [self._property_name_or_number.lower(), self._street_name.lower()]

        matches = []
        for a in address_links:
            text = a.get_text(strip=True).lower()
            if all(word in text for word in required_words):
                matches.append(a)

        # Use the first matching link
        link = matches[0] if matches else None

        return link.get("href") if link else None
    

    def _get_collections(self, session: requests.Session, headers: Dict[str, str], collections: str) -> Any:
        """
        Loads the final schedule page and extracts all collection dates and types.
        """

        # Get the schedule page
        url = f"{API_URL}/{collections}"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Find the section element containing the scheduled collections
        table = soup.find("section", id="scheduled-collections")
        list_items = table.find_all(["ul", "ol"])

        scheduled_dates = []
        scheduled_types = []

        date_match = None
        type_match = None
        
        # Extract each list item containing a date and a service type
        for lst in list_items:
            for li in lst.find_all("li"):
                if li.find('p') is not None:
                    text = li.get_text(strip=True)

                    # Extract date in DD/MM/YYYY format
                    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
                    if date_match:
                        date_str = date_match.group()
                        date = dt.datetime.strptime(date_str, "%d/%m/%Y").date()
                        scheduled_dates.append(date)

                    # Extract service type (matches keys in COLLECTION_TYPES)
                    type_match = re.match(r"(.*) Collection Service", text)
                    if type_match:
                        type_str = type_match.group()
                        scheduled_types.append(type_str)

        # Build Collection objects
        entries = []
        for index, item in enumerate(scheduled_dates):
            type_str = scheduled_types[index]
            type_info = COLLECTION_TYPES.get(type_str)
            entries.append(
                Collection(
                    date=item,
                    t=type_info["title"],
                    icon=type_info["icon"],
                )
            )

        return entries

