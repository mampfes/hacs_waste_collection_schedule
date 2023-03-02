import datetime

from bs4 import BeautifulSoup
import requests
import re
from waste_collection_schedule import Collection

TITLE = "Uttlesford District Council"
DESCRIPTION = "Source for uttlesford.gov.uk, Uttlesford District Council, UK"
URL = "https://www.uttlesford.gov.uk"
TEST_CASES = {
    "Brook Cottage, CM6 1LW": {"house": "29142-Tuesday"},
    "Springfields, CM6 1BP": {"house": "26455-Thursday"}
}

API_URL = "http://bins.uttlesford.gov.uk/collections.php?house={house}"

ICON_MAP = {
    "black": "mdi:trash-can",
    "green": "mdi:recycle",
    "brown": "mdi:food-apple"
}

PICTURE_MAP = {
    "black": "https://bins.uttlesford.gov.uk/img/result-black.png",
    "green": "https://bins.uttlesford.gov.uk/img/result-green.png",
    "brown": "https://bins.uttlesford.gov.uk/img/result-brown.png"
}

TEXT_MAP = {
    "black": "Black (Non-Recyclable)",
    "green": "Green (Dry Recycling)",
    "brown": "Brown (Food Waste)"
}

class Source:
    def __init__(self, house=None):
        self._house = house


    
    def fetch(self):
        q = str(API_URL).format(house=self._house)

        r = requests.get(q)
        r.raise_for_status()

        def trimsuffix(s):                                             
            return re.sub(r'(\d)(st|nd|rd|th)', r'\1', s)
        
        responseContent = r.text

        today = datetime.date.today()

        entries = []

        soup = BeautifulSoup(responseContent, "html.parser")
        table = soup.findAll('table')

        rows = table[1].findAll(lambda tag: tag.name=='tr')

        for row in rows:
            fields = row.findChildren()
            image = row.find("img")
            datestr = fields[3].text
            datestr = trimsuffix(datestr) + " " + today.strftime("%Y")
            date = datetime.datetime.strptime(datestr, '%A %d %B %Y')
            
            # As they don't show the year we need to check if it should actually be next year
            if date.date() < today:
                date.replace(year = today.year + 1)
            
            # As all the image alt text etc is wrong on the website we have to go by the image itself
            if 'green' in image['src']:
                collectiontxt = 'green'
            else:
                collectiontxt = 'black'

            entries.append(
                Collection(
                    date=date.date(),
                    t=TEXT_MAP.get(collectiontxt),
                    picture=PICTURE_MAP.get(collectiontxt),
                    icon=ICON_MAP.get(collectiontxt),
                )
            )
            # Add a second collection entry as all collections include the brown food bin
            collectiontxt = 'brown'
            entries.append(
                Collection(
                    date=date.date(),
                    t=TEXT_MAP.get(collectiontxt),
                    picture=PICTURE_MAP.get(collectiontxt),
                    icon=ICON_MAP.get(collectiontxt),
                )
            )

        return entries
