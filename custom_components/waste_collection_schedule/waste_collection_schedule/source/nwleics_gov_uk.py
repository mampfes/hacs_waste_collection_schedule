from datetime import datetime
from dateutil import parser
from waste_collection_schedule import Collection
import requests
from bs4 import BeautifulSoup


TITLE = "North West Leicestershire District Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source for www.nwleics.gov.uk services for the city of North West Leicestershire District Council, UK"  # Describe your source
URL = "https://my.nwleics.gov.uk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Dunmore": {"uprn": "10002359002"},
    "Station Road": {"uprn": "100030573554"},
}

API_URL = "https://my.nwleics.gov.uk/"


BINS = {
    "Refuse": {"icon": "mdi:trash-can", "name": "General"},
    "Garden Waste": {"icon": "mdi:leaf", "name": "Garden"},
    "Yellow Bag":  {"icon": "mdi:recycle", "name": "Recycling"},
    "Blue Bag":  {"icon": "mdi:recycle", "name": "Recycling"},
    "Red Box":  {"icon": "mdi:recycle", "name": "Recycling"},
   
}



class Source:
    def __init__(self, uprn):
        self._uprn = uprn

    def fetch(self):


   

        r = requests.get(f"{API_URL}/location?put=nwl{self._uprn}&rememberme=0&redirect=%2F")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        refuse = soup.find("ul", {"class": "refuse"})
        li_items=refuse.find_all('li')

        entries = []

        for li in li_items:
            strong_tag = li.find('strong')
            a_tag=li.find('a')
            

            collection_date=parser.parse(strong_tag.contents[0]).date()
            type=a_tag.contents[0]


            entries.append(
                Collection(
                    date = collection_date,  # Collection date
                    t = type,  # Collection type
                    icon = BINS.get(type),  # Collection icon
                    )
                )
      
        return entries



     