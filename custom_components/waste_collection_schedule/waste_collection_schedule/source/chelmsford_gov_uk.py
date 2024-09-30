import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection


TITLE = "Chelmsford City Council"
DESCRIPTION = "Source for Chelmsford City Council, UK"
URL = "https://www.chelmsford.gov.uk/"
COUNTRY = "uk"
TEST_CASES = {
    "Test_001": {"collection_round": "Tuesday A"},
    "Test_002": {"collection_round": "Thursday B"},
}

ICON_MAP = {
    "food waste": "mdi:food-apple",
    "black bin": "mdi:trash-can",
    "brown bin": "mdi:leaf",
    "green box": "mdi:bottle-soda",
    "paper sack": "mdi:newspaper",
    "card sack": "mdi:package-variant",
    "plastic and cartons bag": "mdi:recycle"
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can find your collection round by visiting https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day and entering in your address details.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "collection_round": "Collection round identifier (e.g. Tuesday A). You can find yours by going to https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day and entering in your address details.",
    },
}

class Source:
    def __init__(self, collection_round):
        self._collection_round = collection_round

    def fetch(self) -> list[Collection]:
        url = f"https://www.chelmsford.gov.uk/bins-and-recycling/check-your-collection-day/{self._collection_round.lower().replace(' ', '-')}-collection-calendar/"

        r = requests.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.content, 'html.parser')
        
        divs = soup.find_all('div', class_='textcontent')
        
        entries = []

        for div in divs:
            heading_items = div.find_all(['h2'])
            list_items = div.find_all(['ul', 'ol'])
          
            for list in list_items:
                items = list.find_all('li')
                for item in items:
                    it = item.get_text(strip=True)
                    date_str, items = it.split(':')
                    day, date, month = date_str.split()

                    year = None
                    for h in heading_items:
                        heading = h.get_text(strip=True)
                        if month in heading:
                            year=heading.split()[1]
                            break
                    
                    date = datetime.strptime(f"{date} {month} {year}", "%d %B %Y").date()
                    for i in items.split(','):
                        waste_type=i.strip()
                        entries.append(
                            Collection(
                                date=date,
                                t=waste_type.title(),
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
        return entries
