import datetime
import json
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "City of Monash"
DESCRIPTION = "Source for City of Monash rubbish collection."
URL = "https://www.monash.vic.gov.au/"

TEST_CASES = {
    "Test_001": {"address": "4 Carson Street, Mulgrave 3170"},
    "Test_002": {"address": "57 Hamilton Place, Mount Waverley 3149"},
}

SEARCH_PAGE_URL = f"{URL}Waste-Sustainability/Bin-Collection/When-we-collect-your-bins"
ICON_MAP = {
    "Landfill Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food and Garden Waste": "mdi:leaf",
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": f'Visit the [City of Monash]({SEARCH_PAGE_URL}) "When we collect your bins" page and search for your address. For example: 4 Carson Street, Mulgrave 3170. The arguments should exactly match the full street address after selecting the autocomplete result.',
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Full street address including suburb, state and postal code",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, address:str):  # argX correspond to the args dict in the source configuration
        self._address = address

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        r = s.get(
            f"{URL}api/v1/myarea/search?keywords={self._address.replace(" ", "+")}"
        )
        if r.status_code != requests.codes.ok:
            raise Exception("Error Accessing myarea API") # DO NOT JUST return [] 
        data = r.json()
        geoid = data["Items"][0]["Id"] # assume first one is correct and get geoid
        
        r = s.get(
            f"{URL}ocapi/Public/myarea/wasteservices?geolocationid={geoid}&ocsvclang=en-AU"
        )

        if r.status_code != requests.codes.ok:
            raise Exception("Error Accessing Waste Services API") # DO NOT JUST return []
        schedule = r.json()
        html = r.json()['responseContent']
        soup = BeautifulSoup(html, "html.parser")

        entries = []  # List that holds collection schedule
        for article in soup.find_all("article"):
            waste_type = article.find("h3").get_text(strip=True)

            note = (
                article.find("div", class_="note")
                .get_text(" ", strip=True)
                .replace("Collected ", "")
                .replace(". Your next collection day is:", "")
            )
            next_date_str = article.find("div", class_="next-service").get_text(strip=True)
            next_date = datetime.datetime.strptime(next_date_str, "%a %d/%m/%Y").date()
            entries.append(
                Collection(
                    date = next_date,  # Collection date
                    t = waste_type,  # Collection type
                    icon = ICON_MAP.get(waste_type),  # Collection icon
                )
            )

        return entries
