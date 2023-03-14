import requests
from bs4 import BeautifulSoup
from dateutil import parser
from waste_collection_schedule import Collection

TITLE = "Swindon Borough Council"
DESCRIPTION = "Swindon Borough Council, UK - Waste Collection"
URL = "https://www.swindon.gov.uk"
TEST_CASES = {
    "1 Nyland Road": {"uprn": "100121147490"},
    "74 Standen Way": {"uprn": "200002922415"},
    "1 Eastbury Way": {"uprn": "10010424600"},
    "33 Ulysses Road": {"uprn": "10010427033"}
}

ICON_MAP = {
    "Rubbish bin": "mdi:trash-can",
    "Recycling boxes": "mdi:recycle",
    "Garden waste bin": "mdi:leaf",
    "Plastics": "mdi:sack",
}


class Source:
    def __init__(self, uprn: str):
        self.uprn = uprn
        self.url = f"{URL}/info/20122/rubbish_and_recycling_collection_days?uprnSubmit=Yes&addressList={self.uprn}"

    def fetch(self):
        collection_lookup = requests.post(
            f"{URL}/info/20122/rubbish_and_recycling_collection_days?uprnSubmit=Yes&addressList={self.uprn}"
        )
        collection_lookup.raise_for_status()
        
        entries = []
        for results in BeautifulSoup(collection_lookup.text, "html.parser").find_all(
            "div", class_="bin-collection-content"
        ):
            
            try:
                recyclingdate = results.find("span", class_="nextCollectionDate");
                
                if recyclingdate != None :
                    recyclingtype = results.find('div', class_='content-left').find("h3");
                    entries.append(
                        Collection(
                            date=parser.parse(recyclingdate.text, dayfirst=True).date(),
                            t=recyclingtype.text,
                            icon=ICON_MAP.get(recyclingtype.text),
                        )
                    )
            except (StopIteration, TypeError):
                pass
        return entries