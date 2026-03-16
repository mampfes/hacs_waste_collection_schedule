import datetime
import json
import time

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Woollahra Municipal Council (NSW)"
DESCRIPTION = "Source for Woollahra Municipal Council rubbish collection."
URL = "https://www.woollahra.nsw.gov.au/"
TEST_CASES = {
    "13 Paddington Street Paddington": {
        "address": "13 Paddington Street PADDINGTON NSW 2021",
    },
    "22 Oxford Street Paddington": {
        "address": "22 Oxford Street PADDINGTON NSW 2021",
    },
}

API_URLS = {
    "address_search": "https://www.woollahra.nsw.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.woollahra.nsw.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU&pageLink=/$b9015858-988c-48a4-9473-7c193df083e4$/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Sec-Ch-Ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Priority": "u=0, i",
}

# Constants
CLEANUP_ICON = "mdi:delete-sweep"
DATE_FORMAT_LONG = "%d %B %Y"

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Green Waste": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "Spring Clean-Up": CLEANUP_ICON,
    "Summer Clean-Up": CLEANUP_ICON,
    "Winter Clean-Up": CLEANUP_ICON,
}


class Source:
    def __init__(self, address: str):
        self.address = address.strip()

    def _make_request_with_retry(self, session, url, headers, max_retries=3, timeout=30):
        """Make HTTP request with retry logic and exponential backoff"""
        for attempt in range(max_retries):
            try:
                r = session.get(url, headers=headers, timeout=timeout)
                
                if r.status_code == 200:
                    return r
                elif r.status_code == 403 and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed to fetch: {r.status_code} (attempt {attempt + 1})")
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Network error: {str(e)}")
                time.sleep(2 ** attempt)
        
        raise requests.exceptions.RequestException(
            "Max retries exceeded while fetching URL"
        )

    def fetch(self):
        location_id = None

        address = self.address

        # Create a session to maintain cookies and state
        session = requests.Session()
        session.headers.update(HEADERS)

        # First, visit the main page to establish a session and get cookies
        try:
            main_page_response = session.get(
                "https://www.woollahra.nsw.gov.au/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates", 
                timeout=30
            )
            if main_page_response.status_code not in [200, 403]:
                time.sleep(2)  # Wait a bit if we get an unexpected response
        except requests.RequestException:
            # If we can't access the main page, we might still be able to access the API
            pass

        # Update headers for the API calls
        api_headers = HEADERS.copy()
        api_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.woollahra.nsw.gov.au/Services/Rubbish-and-recycling/Find-your-rubbish-and-scheduled-clean-up-service-dates",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })

        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve address search results with retry logic
        r = self._make_request_with_retry(session, q, api_headers)

        # Handle potential bot protection response
        if r.status_code != 200:
            raise Exception(f"Unable to access Woollahra API (status: {r.status_code}). This may be due to bot protection. Please try again later or contact support.")

        try:
            data = json.loads(r.text)
        except json.JSONDecodeError:
            # Check if we got an HTML error page instead of JSON
            if "Access Denied" in r.text:
                raise Exception("Access denied by Woollahra website. This may be due to bot protection measures. Please try again later.")
            else:
                raise Exception("Invalid JSON response from address search API")

        # Find the ID for our address
        if data.get("Items") and len(data["Items"]) > 0:
            location_id = data["Items"][0]["Id"]
        
        if not location_id:
            raise ValueError(
                f"Unable to find location ID for {address}. Please check your address details are correct."
            )

        time.sleep(1)  # Brief delay between requests

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(location_id))

        # Retry logic for waste services API
        r = self._make_request_with_retry(session, q, api_headers)

        if r.status_code != 200:
            raise Exception(f"Unable to access Woollahra waste services API (status: {r.status_code})")

        try:
            data = json.loads(r.text)
        except json.JSONDecodeError:
            if "Access Denied" in r.text:
                raise Exception("Access denied by Woollahra website during waste services fetch.")
            else:
                raise Exception("Invalid JSON response from waste services API")

        if not data.get("success") or not data.get("responseContent"):
            raise RuntimeError("Invalid response from waste services API")

        response_content = data["responseContent"]

        soup = BeautifulSoup(response_content, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            # Extract the waste type from h3 tag
            waste_type_element = item.find("h3")
            if not waste_type_element:
                continue
                
            waste_type = waste_type_element.text.strip()
            
            # Normalize seasonal cleanup names
            if "spring" in waste_type.lower() and "clean" in waste_type.lower():
                waste_type = "Spring Clean-Up"
            elif "summer" in waste_type.lower() and "clean" in waste_type.lower():
                waste_type = "Summer Clean-Up"
            elif "winter" in waste_type.lower() and "clean" in waste_type.lower():
                waste_type = "Winter Clean-Up"
            
            # Find the date information
            date_element = item.find("div", attrs={"class": "next-service"})
            if not date_element:
                continue
                
            date_text = date_element.text.strip()
            
            # Parse different date formats
            date = self._parse_date(date_text)
            
            if date:
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                    )
                )

        return entries

    def _parse_date(self, date_text: str) -> datetime.date | None:
        """Parse various date formats found in the response"""
        try:
            return dateutil.parser.parse(date_text, dayfirst=True, fuzzy=True).date()
        except (dateutil.parser.ParserError, OverflowError) as e:
            return None