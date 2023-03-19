import datetime
import locale
from xml.etree.ElementTree import tostring
from waste_collection_schedule import Collection
import requests
from bs4 import BeautifulSoup

TITLE = "Esch-sur-Alzette" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for administration.esch.lu, communal website of the city of Esch-sur-Alzette in Luxembourg"  # Describe your source
URL = "https://administration.esch.lu"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Zone A": {"zone": "1"},
    "Zone B": {"zone": "2"}
}

API_URL = "https://administration.esch.lu/dechets/?street=0&tour="
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "Poubelle ménage": "mdi:trash-can",
    "Papier": "mdi:recycle",
    "Organique": "mdi:leaf",
    "Verre": "mdi:bottle-wine-outline",
    "Valorlux": "mdi:recycle",
    "Déchets toxiques": "mdi:skull-crossbones",
    "Container ménage": "train-car-container"
}


""" TEST CODE  """
""" locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8') # set the French locale to import the dates
response = requests.get(API_URL+'1')
soup = BeautifulSoup(response.content, "html.parser")

# Find the table containing the waste collection schedule
table = soup.find('table', {'id': 'garbage-table'})

locale.setlocale(locale.LC_TIME, 'en_US.utf8') # Switch back to English locale

# Extract the waste types and their corresponding collection dates
entries = []
for row in table.find_all('tr'):
    cells = row.find_all('td')
    if len(cells) == 3:
        t = cells[1].text.strip() # Collection type
        if t.startswith("Cartons en vrac"): continue
        if t.startswith("Déchets toxiques"): t = "Déchets toxiques"
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8') # set the French locale to import the dates
        date = datetime.datetime.strptime(cells[2].text.strip(),"%A, %d %B %Y") # Collection date
        locale.setlocale(locale.LC_TIME, 'en_US.utf8') # Switch back to English locale
        date = date.strftime("%Y%m%d")
        icon = ICON_MAP.get(t),  # Collection icon
        entry = [date, t,icon]
        entries.append(entry)
 


for entry in entries:
    print(entry[0], entry[1], entry[2])

"""


class Source:
    def __init__(self, zone):  # argX correspond to the args dict in the source configuration
        self._zone = zone

    def fetch(self):

        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8') # set the French locale to import the dates
        response = requests.get(API_URL+self._zone)
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table containing the waste collection schedule
        table = soup.find('table', {'id': 'garbage-table'})
        locale.setlocale(locale.LC_TIME, 'en_US.utf8') # Switch back to English locale

        entries = []  # List that holds collection schedule
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 3:
                t = cells[1].text.strip() # Collection type
                if t.startswith("Cartons en vrac"): continue # Skip the cardboard collection for companies
                if t.startswith("Déchets toxiques"): t = "Déchets toxiques" # Remove collecting insrtuctions
                locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8') # set the French locale to import the dates
                date = datetime.datetime.strptime(cells[2].text.strip(),"%A, %d %B %Y").date() # Collection date
                locale.setlocale(locale.LC_TIME, 'en_US.utf8') # Switch back to English locale
                #date = date.strftime("%Y%m%d")
                icon = ICON_MAP.get(t),  # Collection icon
                entries.append(Collection(date,t,icon)) #append current entry
        return entries