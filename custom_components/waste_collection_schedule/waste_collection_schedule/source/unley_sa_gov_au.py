import datetime
import json

import requests
from bs4 import BeautifulSoup
from requests.utils import requote_uri
from waste_collection_schedule import Collection

TITLE = "Unley City Council (SA)"
DESCRIPTION = "Source for Unley City Council rubbish collection."
URL = "https://www.unley.sa.gov.au/"
TEST_CASES = {
    "Test1": {
        "post_code": "5061",
        "suburb": "Malvern",
        "street_name": "Wattle Street",
        "street_number": "188",
    },
    "Test2": {
        "post_code": 5061,
        "suburb": "Unley",
        "street_name": "Unley Road",
        "street_number": "192",
    },
    "Test3": {
        "post_code": "5063",
        "suburb": "Parkside",
        "street_name": "Castle Street",
        "street_number": "63",
    },
}

API_URLS = {
    "address_search": "https://www.unley.sa.gov.au/api/v1/myarea/search?keywords={}",
    "collection": "https://www.unley.sa.gov.au/ocapi/Public/myarea/wasteservices?geolocationid={}&ocsvclang=en-AU",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

ICON_MAP = {
    "General Waste (Blue Bin)": "mdi:trash-can",
    "Organic Waste (Green or Grey Bin)": "mdi:leaf",
    "Recycling (Yellow Lid Bin)": "mdi:recycle",
    "Residential Street Cleaning": "mdi:broom",
    # Fallback patterns
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Green Waste": "mdi:leaf",
}

class Source:
    def __init__(
        self, post_code: str, suburb: str, street_name: str, street_number: str
    ):
        self.post_code = post_code
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number

    def fetch(self):
        locationId = ""

        address = "{} {} {} SA {}".format(
            self.street_number, self.street_name, self.suburb, self.post_code
        )

        q = requote_uri(str(API_URLS["address_search"]).format(address))

        # Retrieve address search results
        r = requests.get(q, headers=HEADERS)
        r.raise_for_status()

        # Parse XML response (API returns XML, not JSON)
        soup = BeautifulSoup(r.text, 'xml')
        
        # Look for PhysicalAddressSearchResult items in the XML response
        address_results = soup.find_all('PhysicalAddressSearchResult')
        
        # Find the ID for our address
        for result in address_results:
            id_element = result.find('Id')
            if id_element:
                locationId = id_element.text.strip()
                break

        if not locationId:
            return []

        # Retrieve the upcoming collections for our property
        q = requote_uri(str(API_URLS["collection"]).format(locationId))

        r = requests.get(q, headers=HEADERS)
        r.raise_for_status()

        # Parse JSON response and extract HTML content
        data = json.loads(r.text)
        responseContent = data["responseContent"]

        soup = BeautifulSoup(responseContent, "html.parser")
        services = soup.find_all("div", attrs={"class": "waste-services-result"})

        entries = []

        for item in services:
            date_text = item.find("div", attrs={"class": "next-service"})
            waste_type = item.find("h3")
            
            if not date_text or not waste_type:
                continue
                
            try:
                # Parse the date (format: "Thu 7/8/2025")
                cleaned_date_text = date_text.text.replace('\r','').replace('\n','').strip()
                date = datetime.datetime.strptime(cleaned_date_text, '%a %d/%m/%Y').date()
                
                waste_type_text = waste_type.text.strip()

                entries.append(
                    Collection(
                        date=date,
                        t=waste_type_text,
                        icon=ICON_MAP.get(waste_type_text, "mdi:trash-can"),
                    )
                )
            except (ValueError, AttributeError):
                continue

        return entries
