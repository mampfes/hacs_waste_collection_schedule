import urllib.request
from bs4 import BeautifulSoup
from dateutil import parser
import logging
from waste_collection_schedule import Collection

TITLE = "Sheffield.gov.uk"

DESCRIPTION = (
    "Source for waste collection services from Sheffield City Council (SCC)"
)

# Base URL for waste collection services
URL = "https://wasteservices.sheffield.gov.uk/"

# Headers to mimic the browser
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

TEST_CASES = {
    # These are random addresses around Sheffield
    # If your property is listed here and you don't want it, please raise an issue and I'll amend
    "test001" : {"uprn": "100050938234"},
    "test002" : {"uprn": "100050961380"},
    "test003" : {"uprn": "100050920796"},
}

# Icons for the different bin types
ICONS = {
    "BLACK": "mdi:delete-empty", # General Waste
    "BROWN": "mdi:glass-fragile", # Glass, Tins, Cans & Plastics
    "BLUE": "mdi:newspaper", # Paper & Cardboard
    "GREEN": "mdi:leaf", # Garden Waste
}

_LOGGER = logging.getLogger(__name__)

class Source:
    def __init__(self, uprn=None):
        self._uprn = str(uprn)

    def fetch(self):
        if self._uprn:
            # Get the page containing bin details
            # /calendar gives further future informaion over just the "Services" page
            req = urllib.request.Request(f"{URL}/property/{self._uprn}/calendar",headers=HEADERS)
            with urllib.request.urlopen(req) as response:
                html_doc = response.read()

            # Parse the page to get the data required (collection date and type)
            soup = BeautifulSoup(html_doc, 'html.parser')
            entries = []
            # Find all entries relating to bin collection & loop through them
            for collection in soup.find_all('div',{"class":"calendar-table-cell"}):
                try:
                    # The collection details are in the title field of each ul/li
                    # Converting date from title field to a usable format
                    collection_date = parser.parse(collection.ul.li['title'].split(" - ")[0]).date()
                    # Getting the collection type
                    collection_type = collection.ul.li['title'].split(" - ")[1]

                    # Append to entries for main program
                    entries.append(
                        Collection(
                            date = collection_date,
                            t = collection_type,
                            icon = ICONS.get(collection_type.replace(" Bin","").upper()),
                        )
                    )
                except ValueError:
                    pass

        return entries