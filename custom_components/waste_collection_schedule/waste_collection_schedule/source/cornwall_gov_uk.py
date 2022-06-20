from waste_collection_schedule import Collection
from datetime import datetime, date
from bs4 import BeautifulSoup
import requests

TITLE = "Cornwall Council, UK"
DESCRIPTION = "Source for cornwall.gov.uk services for Cornwall Council"
URL = "cornwall.gov.uk"
TEST_CASES = { 
    "known_uprn": { "uprn" : "100040118005" },
    "unknown_uprn": { "postcode": "TR261SP", "housenumberorname":"7"},
}
SEARCH_URLS = {
    "uprn_search" : "https://www.cornwall.gov.uk/my-area/",
    "collection_search" : "https://www.cornwall.gov.uk/umbraco/Surface/Waste/MyCollectionDays?subscribe=False"
}
COLLECTIONS = [
    {"name" : "rubbish", "description" : "Rubbish" },
    {"name" : "recycling", "description" : "Recycling" },
]   

class Source:
    def __init__(self, uprn=None, postcode=None, housenumberorname=None): # argX correspond to the args dict in the source configuration
        self._uprn = uprn
        self._postcode = postcode
        self._housenumberorname = housenumberorname

    def fetch(self):
        entries = []
        session = requests.Session()

        # Find the UPRN based on the postcode and the property name/number
        if self._uprn is None:
            args = {
                "Postcode" : self._postcode
            }
            r = session.get(
                SEARCH_URLS['uprn_search'], params=args
            )
            soup = BeautifulSoup(r.text, features="html.parser")
            propertyUprns = soup.find(id="Uprn").find_all('option')
            for match in propertyUprns:
                if match.text.startswith(self._housenumberorname):
                    self._uprn = match['value']

        # Get the collection days based on the UPRN (either supplied through arguments or searched for above)
        if self._uprn is not None:
            args = {
                "uprn" : self._uprn
            }
            r = session.get(
                SEARCH_URLS['collection_search'], params=args
            )
            soup = BeautifulSoup(r.text, features="html.parser")
            for collection in COLLECTIONS:
                # Find the dates and format it correctly
                d = soup.find(id=collection['name']).find_all('span')[-1].text + ' ' + str(date.today().year)
                # Add each entry
                entries.append(
                    Collection(
                        datetime.strptime(d, "%d %b %Y").date(),
                        collection['description'],
                    )
                )
        else:
            return []

        return entries
