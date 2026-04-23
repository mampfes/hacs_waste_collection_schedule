import datetime

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Richmond upon Thames"
DESCRIPTION = "Source for London Borough of Richmond upon Thames"
URL = "https://www.richmond.gov.uk/"

TEST_CASES = {
    "Rosemont Road": {"uprn": "100022315214"},
    "Bryanston Avenue": {"uprn": "100022330653"},
    "Spring Grove Road": {"uprn": "100022317336"},
}

API_URL = "https://www.richmond.gov.uk/my_richmond"

ICON_MAP = {
    "Glass, can, plastic and carton recycling": "mdi:recycle",
    "Paper and card recycling": "mdi:newspaper-variant",
    "Rubbish and food": "mdi:trash-can",
    "Garden waste": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {"uprn": "Property UPRN (Unique Property Reference Number)"},
    "de": {"uprn": "UPRN der Immobilie"},
    "it": {"uprn": "UPRN della proprietà"},
    "fr": {"uprn": "UPRN du bien"},
}

PARAM_DESCRIPTIONS = {
    "en": {"uprn": "Find your UPRN at https://www.findmyaddress.co.uk/"},
    "de": {"uprn": "Finden Sie Ihre UPRN unter https://www.findmyaddress.co.uk/"},
    "it": {"uprn": "Trova il tuo UPRN su https://www.findmyaddress.co.uk/"},
    "fr": {"uprn": "Trouvez votre UPRN sur https://www.findmyaddress.co.uk/"},
}

# Strict allowlist of valid waste collection services
ALLOWED_SERVICES = set(ICON_MAP.keys())

class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        params = {"pid": self._uprn}
        headers = {"User-Agent": "Mozilla/5.0"}

        try:
            response = requests.get(
                API_URL,
                params=params,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise Exception("API request timed out")
        except requests.RequestException as e:
            raise Exception(f"API request failed: {e}")

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Check if the property exists/valid by looking for the waste section
        waste_div = soup.find("div", class_="my-waste")
        if not waste_div:
            # If the jumbotron says "Search" or is empty, the UPRN is likely wrong
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []

        # Find all <h4> headers (waste types) inside the waste div
        for h4 in waste_div.find_all("h4"):
            service_name = h4.get_text(strip=True)
            
            if service_name not in ALLOWED_SERVICES:
                continue
            
            # The date is usually in the next <ul> <li> sibling
            ul_sibling = h4.find_next_sibling("ul")
            if not ul_sibling:
                continue

            li_text = ul_sibling.get_text(strip=True)
            
            # Logic to ignore text-only entries (like missing garden waste contracts)
            if "No collection contract" in li_text:
                continue

            try:
                # Richmond dates look like: "Tuesday 21 April 2026"
                # We split and take the last 3 parts: "21 April 2026"
                date_parts = li_text.split()
                if len(date_parts) < 3:
                    continue
                    
                date_str = " ".join(date_parts[-3:])
                collection_date = datetime.datetime.strptime(
                    date_str, "%d %B %Y"
                ).date()
                
                entries.append(
                    Collection(
                        date=collection_date,
                        t=service_name,
                        icon=ICON_MAP.get(service_name, "mdi:trash-can"),
                    )
                )
            except (ValueError, IndexError):
                continue

        if not entries:
            raise Exception("No valid waste collection entries found for this UPRN")

        return entries