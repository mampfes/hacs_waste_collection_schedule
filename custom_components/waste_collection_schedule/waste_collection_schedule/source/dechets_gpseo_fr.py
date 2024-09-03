import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # Import Collection class
from datetime import datetime
from datetime import timedelta
import re

TITLE = "GPSEO Waste Collection"
DESCRIPTION = "Source for GPSEO waste collection services."
URL = "https://dechets.gpseo.fr/"
COUNTRY = "fr"

TEST_CASES = {
    "Formatted Address Test": {"address": "11-rue-jean-moulin-mantes-la-ville"},
    "Unformatted Address Test": {"address": "157 rue maurice utrillo, villennes sur seine"}
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
    def _get_correct_url(self, first_try=True):
        params = {'q': self.address}
        if not first_try:
            # Remove any additional information from the address
            params={'q': re.split(r'[,-]', self.address)[0].strip()}

        # Step 1: Send a POST request to the autocomplete endpoint with the user's address
        autocomplete_url = "https://dechets.gpseo.fr/views-autocomplete-filters/collecte_des_dechets_rue/block_rues/title/0"
        response = requests.get(autocomplete_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from {autocomplete_url}: {response.status_code}")

        # Parse the JSON response to get the formatted URL
        try:
            data = response.json()
            if not data:
                if first_try:
                    return self._get_correct_url(first_try=False)
                raise Exception("No results returned from autocomplete.")
        except ValueError:
            raise Exception("Failed to parse JSON response.")
        URL_REGEX = r'<a href="(.+?)".+?>(.*?)</a>'
        compareable_address = self.address.lower().replace(" ", "")
        addresses = []
        for result_intem in data:
            addresses.append(result_intem['value'].split('-')[0].strip())
            comparable_match = result_intem['value'].lower().replace(" ", "")
            if comparable_match.replace(",", "").replace("-", "") == compareable_address.replace(",", "").replace("-", "") or compareable_address in comparable_match.split("-"):
                html = result_intem['label'].encode().decode('unicode_escape')
                url = re.search(URL_REGEX, html)
                if url:
                    return f"https://dechets.gpseo.fr{url.group(1)}"
            
        raise Exception("Could not find the correct address, available addresses: " + ", ".join(addresses))
    
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
            block = soup.find('div', class_=f'wrapper-block {waste_class}')
            
            if block:
                print(f"Found block for: {waste_name}")
                # Look for the date-event field within the block
                date_block = block.find('div', class_='field--name-field-date-event')
                if date_block:
                    date_items = date_block.find_all('div', class_='field__item')
                    for item in date_items:
                        date_str = item.text.strip()
                        date = self._parse_date(date_str)
                        if date:
                            entries.append(Collection(date, waste_name, icon=ICON_MAP.get(waste_class)))
                else:
                    print(f"No date-event field found within block for {waste_name}")
            else:
                print(f"No block found for: {waste_name}")
        
        print(f"Entries found: {len(entries)}")
        return entries

    def _parse_date(self, date_str):
        # Map French days of the week to integers
        days_of_week = {
            "lundi": 0,
            "mardi": 1,
            "mercredi": 2,
            "jeudi": 3,
            "vendredi": 4,
            "samedi": 5,
            "dimanche": 6
        }
        
        # Extract time of day if specified
        if "matin" in date_str:
            time_of_day = "morning"
        elif "après-midi" in date_str:
            time_of_day = "afternoon"
        else:
            time_of_day = "night before"  # Default assumption
        
        # Extract the day of the week
        for day in days_of_week.keys():
            if day in date_str:
                today = datetime.now()
                current_weekday = today.weekday()
                target_weekday = days_of_week[day]

                # Calculate the next occurrence of the target weekday
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                collection_date = today + timedelta(days=days_ahead)
                
                # Adjust the date based on the time of day
                if time_of_day == "night before":
                    collection_date -= timedelta(days=1)

                return collection_date.date()
        
        # Try parsing dates like "12 septembre"
        try:
            return datetime.strptime(date_str, "%d %B").replace(year=datetime.now().year).date()
        except ValueError:
            return None
        
    def _extract_date(self, text):
        # Extract date using regex
        match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
        if match:
            return match.group(1)
        return None