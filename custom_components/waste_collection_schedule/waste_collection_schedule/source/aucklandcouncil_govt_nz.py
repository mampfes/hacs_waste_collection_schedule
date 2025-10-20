import datetime

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
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # New site structure uses <p class="mb-0 lead"> with icon and text
        # Example: <p class="mb-0 lead"><span class="acpl-icon-with-attribute left">
        #          <i class="acpl-icon rubbish"></i>...<b>Monday, 20 October</b></span></p>
        
        for p in soup.find_all("p", class_="mb-0 lead"):
            # Find the icon to determine waste type
            icon = p.find("i", class_=lambda x: x and "acpl-icon" in x)
            if not icon:
                continue
            
            # Extract waste type from icon classes
            classes = icon.get("class", [])
            rubbish_type = None
            for c in classes:
                if c != "acpl-icon":
                    rubbish_type = c
                    break
            
            if not rubbish_type:
                continue
            
            # Find the date - it's in a <b> tag within the paragraph
            date_tag = p.find("b")
            if not date_tag:
                continue
            
            date_str = date_tag.text.strip()
            if not date_str:
                continue
            
            try:
                collection_date = toDate(date_str)
                entries.append(Collection(collection_date, rubbish_type))
            except (ValueError, KeyError, IndexError) as e:
                # Skip entries with invalid dates
                continue

        if not entries:
            raise Exception(f"No collection data found for area {self._area_number}. The page structure may have changed or the area number may be invalid.")

        return entries
