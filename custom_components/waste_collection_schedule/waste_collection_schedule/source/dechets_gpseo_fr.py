import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # Import Collection class
from datetime import datetime
import re

TITLE = "GPSEO Waste Collection"
DESCRIPTION = "Source for GPSEO waste collection services."
URL = "https://dechets.gpseo.fr/"
COUNTRY = "fr"

TEST_CASES = {
    "Formatted Address Test": {"address": "11-rue-jean-moulin-mantes-la-ville"},
    "Unformatted Address Test": {"address": "157 rue maurice utrillo, villennes sur seine"},
    "Another Unformatted Address Test": {"address": "15 rue de la chenille, Verneuil sur seine"}
}

ICON_MAP = {
    "ordures-menageres": "mdi:trash-can",
    "emballages": "mdi:bottle-soda",
    "encombrants": "mdi:leaf",
    "dechets-verts": "mdi:package-variant",
    "verres": "mdi:recycle",
}

class Source:
    def __init__(self, address):
        self.address = address
        # Check if the address is already formatted or not
        if '-' in address:
            self._url = f"https://dechets.gpseo.fr/vivre-et-habiter/gerer-mes-dechets/mes-jours-de-collecte/{address}"
        else:
            self._url = self._get_correct_url()

    def _get_correct_url(self):
        # Step 1: Send a POST request to the autocomplete endpoint with the user's address
        autocomplete_url = "https://dechets.gpseo.fr/views-autocomplete-filters/collecte_des_dechets_rue/block_rues/title/0"
        response = requests.post(autocomplete_url, data={'title': self.address})

        if response.status_code != 200:
            raise Exception(f"Error fetching data from {autocomplete_url}: {response.status_code}")

        # Parse the JSON response to get the formatted URL
        try:
            data = response.json()
            if not data:
                raise Exception("No results returned from autocomplete.")
        except ValueError:
            raise Exception("Failed to parse JSON response.")

        # Extract the URL part (assuming the first match is the correct one)
        result = data[0]
        formatted_address = result['url']
        
        # Construct the final URL for waste collection data
        correct_url = f"https://dechets.gpseo.fr{formatted_address}"
        return correct_url

    def fetch(self):
        # Send a GET request to the page
        response = requests.get(self._url)

        if response.status_code != 200:
            raise Exception(f"Error fetching data from {self._url}: {response.status_code}")

        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Define the list of blocks to scrape
        waste_types = {
            'ordures-menageres': "Ordures Ménagères",
            'emballages': "Emballages",
            'encombrants': "Encombrants",
            'dechets-verts': "Déchets Verts",
            'verres': "Verres"
        }

        # List to hold collection entries
        entries = []

        # Loop through each waste type and extract the relevant information
        for waste_class, waste_name in waste_types.items():
            block = soup.find('div', class_=f'block-wrapper-{waste_class}')
            
            if block:
                # Get the collection schedule details
                details = block.find('div', class_='planning-content').text.strip()
                
                # Parse dates from the details (Assuming dates are included in a readable format)
                for line in details.split('\n'):
                    date_str = self._extract_date(line)
                    if date_str:
                        date = datetime.strptime(date_str, "%d/%m/%Y").date()
                        entries.append(Collection(date, waste_name, icon=ICON_MAP.get(waste_class)))
        
        return entries

    def _extract_date(self, text):
        # Extract date using regex
        match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if match:
            return match.group(1)
        return None