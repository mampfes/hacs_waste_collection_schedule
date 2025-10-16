import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Auckland Council"
DESCRIPTION = "Source for Auckland council."
URL = "https://new.aucklandcouncil.govt.nz"

TEST_CASES = {
    "429 Sea View Road": {"area_number": "12342453293"},  # Monday
    "8 Dickson Road": {"area_number": 12342306525},  # Thursday
    "with Food Scraps": {"area_number": 12341998652},
    "3 Andrew Road": {"area_number": "12345375455"},  # friday with foodscraps
}

MONTH = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def toDate(formattedDate: str, year: int | None = None) -> datetime.date:
    # formattedDate looks like "Wednesday, 8 October"
    parts = formattedDate.replace(",", "").split()
    # ["Wednesday", "8", "October"]
    day = int(parts[1])
    month = MONTH[parts[2]]
    if year is None:
        today = datetime.date.today()
        year = today.year
        # Handle December rollover into January
        if month == 1 and today.month == 12:
            year += 1
    return datetime.date(year, month, day)


HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}


class Source:
    def __init__(self, area_number: str | int):
        self._area_number = str(area_number)

    def fetch(self) -> list[Collection]:
        url = f"https://new.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{self._area_number}.html"
        r = requests.get(url, headers=HEADER)

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Find only the household collection section
        # Look for the card with "Household collection" title
        household_section = None
        schedule_cards = soup.find_all("div", class_="acpl-schedule-card")
        
        for card in schedule_cards:
            title_element = card.find("h4", class_="card-title")
            if title_element and "Household collection" in title_element.get_text():
                household_section = card
                break
        
        if not household_section:
            return entries
        
        # Look for collection information only within the household section
        collection_paragraphs = household_section.find_all("p", class_="mb-0 lead")
        
        for p in collection_paragraphs:
            # Look for icon elements
            icon = p.find("i", class_=lambda x: x and "acpl-icon" in x)
            if not icon:
                continue
                
            # Extract the collection type from icon classes
            classes = icon.get("class", [])
            collection_type = None
            for cls in classes:
                if cls in ["rubbish", "recycle", "food-waste"]:
                    collection_type = cls
                    break
            
            if not collection_type:
                continue
                
            # Look for date in bold text within the paragraph
            date_bold = p.find("b")
            if not date_bold:
                continue
                
            date_text = date_bold.get_text(strip=True)
            
            # Extract date from text using regex
            date_match = re.search(r'([A-Za-z]+,\s+\d+\s+[A-Za-z]+)', date_text)
            if not date_match:
                continue
                
            try:
                collection_date = toDate(date_match.group(1))
                # Normalize collection type names
                if collection_type == "food-waste":
                    collection_type = "food scraps"
                elif collection_type == "recycle":
                    collection_type = "recycling"
                    
                entries.append(Collection(collection_date, collection_type))
            except (ValueError, KeyError):
                continue

        return entries