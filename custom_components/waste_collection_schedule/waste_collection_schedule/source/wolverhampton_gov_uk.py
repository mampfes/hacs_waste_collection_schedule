import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wolverhampton City Council"
DESCRIPTION = "Source for Wolverhampton City Council waste collection."
URL = "https://www.wolverhampton.gov.uk"
EXTRA_INFO = [
    {
        "title": "Find My Nearest",
        "description": "Find your waste collection schedule",
        "url": "https://www.wolverhampton.gov.uk/find-my-nearest",
    }
]

TEST_CASES = {
    "Test Case": {"postcode": "WV1 1RD", "uprn": "10094887108"},
}

ICON_MAP = {
    "general_waste": "mdi:trash-can",
    "recycling_waste": "mdi:recycle",
    "garden_waste": "mdi:leaf",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.replace(" ", "").upper()
        self._uprn = uprn

    def fetch(self):
        # First request to get session cookies
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Make the actual request for bin collection data
        url = f"https://www.wolverhampton.gov.uk/find-my-nearest/{self._postcode}/{self._uprn}"
        
        try:
            r = session.get(url, allow_redirects=True, timeout=30)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching data from Wolverhampton Council: {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Find all waste containers
        waste_containers = soup.find_all('div', class_='col-md-4')
        
        for container in waste_containers:
            waste_type_tag = container.find('h3')
            day_tag = container.find('h4')
            next_date_tag = day_tag.find_next_sibling('h4') if day_tag else None
            
            if waste_type_tag and day_tag and next_date_tag:
                # Extract waste type and format it
                waste_type_raw = waste_type_tag.text.strip()
                waste_type_key = waste_type_raw.replace(' ', '_').lower()
                
                # Extract next collection date
                next_date_text = next_date_tag.text.replace('Next date: ', '').strip()
                
                try:
                    # Parse the date (format: "Month Day, Year")
                    date_obj = datetime.strptime(next_date_text, '%B %d, %Y').date()
                    
                    # Map the waste type to our standard types for icons
                    if "general" in waste_type_key or "refuse" in waste_type_key:
                        icon_key = "general_waste"
                    elif "recycl" in waste_type_key:
                        icon_key = "recycling_waste"
                    elif "garden" in waste_type_key or "food" in waste_type_key:
                        icon_key = "garden_waste"
                    else:
                        icon_key = waste_type_key
                    
                    entries.append(
                        Collection(
                            date=date_obj,
                            t=waste_type_raw,  # Use the original waste type name
                            icon=ICON_MAP.get(icon_key, "mdi:trash-can")
                        )
                    )
                except ValueError:
                    # If date parsing fails, try to log it but continue
                    continue

        return entries