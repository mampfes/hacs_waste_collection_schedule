import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequired

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
    "Test Case": {"postcode": "WV1 1SH", "uprn": "10092023592"},
}

ICON_MAP = {
    "General Waste": "mdi:trash-can",
    "Recycling Waste": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
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
            r = session.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SourceArgumentRequired(f"Error fetching data from Wolverhampton Council: {e}")

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Find the bin collection section
        bin_section = soup.find("div", {"id": "bin-collection-days"})
        if not bin_section:
            return entries

        # Look for each waste type section
        for waste_type in ["General Waste", "Recycling Waste", "Garden Waste"]:
            waste_div = bin_section.find("div", text=lambda x: x and waste_type in x if x else False)
            if waste_div:
                # Find the next collection date
                date_text = waste_div.find_next("div", class_="collection-date")
                if date_text:
                    try:
                        date = datetime.strptime(date_text.text.strip(), "%d/%m/%Y").date()
                        entries.append(
                            Collection(
                                date=date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type, "mdi:trash-can")
                            )
                        )
                    except ValueError:
                        continue

        return entries