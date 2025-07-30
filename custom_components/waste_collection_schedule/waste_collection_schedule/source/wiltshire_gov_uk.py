from datetime import date, datetime
import json
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Wiltshire Council"
DESCRIPTION = "Source for wiltshire.gov.uk services for Wiltshire Council"
URL = "https://wiltshire.gov.uk"
TEST_CASES = {
    "standard_uprn": {"uprn": "100121085972", "postcode": "BA149QP"},
    "short_uprn": {"uprn": "10093279003", "postcode": "SN128FF"},
    "padded_uprn": {"uprn": "010093279003", "postcode": "SN128FF"},
}

SEARCH_URLS = {
    "address_search": "https://ilforms.wiltshire.gov.uk/wastecollectiondays/addresslist",
    "collection_search": "https://ilforms.wiltshire.gov.uk/wastecollectiondays/wastecollectioncalendar"
}

COLLECTIONS = {
    "Household waste",
    "Mixed dry recycling (blue lidded bin)",
    "Mixed dry recycling (blue lidded bin) and glass (black box or basket)",
    "Chargeable garden waste",
}

ICON_MAP = {
    "Household waste": "mdi:trash-can",
    "Mixed dry recycling (blue lidded bin)": "mdi:recycle",
    "Mixed dry recycling (blue lidded bin) and glass (black box or basket)": "mdi:recycle",
    "Chargeable garden waste": "mdi:leaf",
}


def add_month(date_):
    if date_.month < 12:
        date_ = date_.replace(month=date_.month + 1)
    else:
        date_ = date_.replace(year=date_.year + 1, month=1)
    return date_


def map_round_type_to_collection(round_type_name):
    """Map API round type names to our standard collection types"""
    mapping = {
        'Chargeable garden waste': 'Chargeable garden waste',
        'CGW': 'Chargeable garden waste',
        'Household waste': 'Household waste',
        'HW': 'Household waste',
        'Mixed dry recycling (blue lidded bin)': 'Mixed dry recycling (blue lidded bin)',
        'MDR': 'Mixed dry recycling (blue lidded bin)',
        'Mixed dry recycling (blue lidded bin) and glass (black box or basket)': 'Mixed dry recycling (blue lidded bin) and glass (black box or basket)',
        'MDRG': 'Mixed dry recycling (blue lidded bin) and glass (black box or basket)'
    }
    
    return mapping.get(round_type_name)


class Source:
    def __init__(
        self, uprn=None, postcode=None
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = str(uprn).zfill(12)  # pad uprn to 12 characters
        self._postcode = postcode

    def fetch(self):
        fetch_month = date.today().replace(day=1)

        entries = []
        for i in range(0, 3):  # Reduced from 7 to 3 months for better performance
            entries.extend(self.fetch_month(fetch_month))
            fetch_month = add_month(fetch_month)

        return entries

    def fetch_month(self, fetch_month):
        """Fetch collection data for a specific month using the new API"""
        
        # Use PropertyRef instead of Uprn for the new API
        params = {
            "Postcode": self._postcode,
            "PropertyRef": self._uprn,
            "Month": fetch_month.month,
            "Year": fetch_month.year,
        }

        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://ilforms.wiltshire.gov.uk/wastecollectiondays',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        r = requests.post(SEARCH_URLS["collection_search"], data=params, headers=headers, timeout=10)
        r.raise_for_status()

        return self.parse_response(r.text)

    def parse_response(self, html):
        """Parse the HTML response to extract collection dates from the new API format"""
        entries = []
        
        # Extract the modelData JSON from the JavaScript in the HTML
        match = re.search(r'modelData\s*=\s*({.*?});', html)
        if match:
            try:
                json_data = json.loads(match.group(1))
                
                if json_data and 'MonthCollectionDates' in json_data:
                    for collection in json_data['MonthCollectionDates']:
                        if 'Date' in collection and 'RoundTypeName' in collection:
                            # Parse the .NET date format (/Date(timestamp)/)
                            date_match = re.search(r'/Date\((\d+)\)/', collection['Date'])
                            if date_match:
                                timestamp = int(date_match.group(1)) / 1000  # Convert milliseconds to seconds
                                collection_date = datetime.fromtimestamp(timestamp).date()
                                
                                # Map the round type names to our collection types
                                collection_type = map_round_type_to_collection(collection['RoundTypeName'])
                                
                                if collection_type:
                                    entries.append(
                                        Collection(
                                            collection_date,
                                            collection_type,
                                            icon=ICON_MAP.get(collection_type),
                                        )
                                    )
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # If JSON parsing fails, try the legacy method
                entries = self.parse_response_legacy(html)
        else:
            # Fallback to legacy parsing if no JSON data found
            entries = self.parse_response_legacy(html)
            
        return entries

    def parse_response_legacy(self, html):
        """Legacy parsing method for older API format (fallback)"""
        soup = BeautifulSoup(html, "html.parser")

        entries = []
        for collection in COLLECTIONS:
            for tag in soup.find_all(attrs={"data-original-title": collection}):
                try:
                    entries.append(
                        Collection(
                            datetime.strptime(
                                tag["data-original-datetext"], "%A %d %B, %Y"
                            ).date(),
                            collection,
                            icon=ICON_MAP.get(collection),
                        )
                    )
                except (KeyError, ValueError):
                    # Skip if we can't parse the date
                    continue
        return entries