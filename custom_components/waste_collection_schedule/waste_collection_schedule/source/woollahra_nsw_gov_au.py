import datetime
import json
import re
import time

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
    "Spring 2025 scheduled clean-up date": CLEANUP_ICON,
    "Summer 2026 scheduled clean-up date": CLEANUP_ICON,
    "Winter 2026 scheduled clean-up date": CLEANUP_ICON,
}


class Source:
    def __init__(self, address: str):
        self.address = address.strip()

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
        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = session.get(q, headers=api_headers, timeout=30)
                
                if r.status_code == 200:
                    break
                elif r.status_code == 403 and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed to fetch address search: {r.status_code} (attempt {attempt + 1})")
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Network error during address search: {str(e)}")
                time.sleep(2 ** attempt)

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
        for attempt in range(max_retries):
            try:
                r = session.get(q, headers=api_headers, timeout=30)
                
                if r.status_code == 200:
                    break
                elif r.status_code == 403 and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception(f"Failed to fetch waste services: {r.status_code} (attempt {attempt + 1})")
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Network error during waste services fetch: {str(e)}")
                time.sleep(2 ** attempt)

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

    def _parse_date(self, date_text: str) -> datetime.date:
        """Parse various date formats found in the response"""
        
        # Clean up the date text
        date_text = date_text.replace("\r", "").replace("\n", "").strip()
        
        # For regular collections: "Mon 29/9/2025"
        regular_date_match = re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2}/\d{1,2}/\d{4})", date_text)
        if regular_date_match:
            try:
                date_str = regular_date_match.group(2)
                return datetime.datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                pass
        
        # For scheduled clean-ups: "Mon 8 September 2025"
        cleanup_date_match = re.search(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", date_text)
        if cleanup_date_match:
            try:
                day = cleanup_date_match.group(2)
                month_name = cleanup_date_match.group(3)
                year = cleanup_date_match.group(4)
                date_str = f"{day} {month_name} {year}"
                return datetime.datetime.strptime(date_str, DATE_FORMAT_LONG).date()
            except ValueError:
                pass
        
        # Alternative format: "5 January 2026"
        alt_date_match = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", date_text)
        if alt_date_match:
            try:
                day = alt_date_match.group(1)
                month_name = alt_date_match.group(2)
                year = alt_date_match.group(3)
                date_str = f"{day} {month_name} {year}"
                return datetime.datetime.strptime(date_str, DATE_FORMAT_LONG).date()
            except ValueError:
                pass
        
        # Alternative format: "15 June 2026"
        june_date_match = re.search(r"(\d{1,2})\s+June\s+(\d{4})", date_text)
        if june_date_match:
            try:
                day = june_date_match.group(1)
                year = june_date_match.group(2)
                date_str = f"{day} June {year}"
                return datetime.datetime.strptime(date_str, DATE_FORMAT_LONG).date()
            except ValueError:
                pass
                
        return None