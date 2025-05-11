import datetime
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound, SourceArgAmbiguousWithSuggestions

TITLE = "Québec (QC)"
DESCRIPTION = "Source script for Québec city waste collection"
URL = "https://www.ville.quebec.qc.ca/services/info-collecte/"
TEST_CASES = {
    "matching address": {"street_number_and_name": "1935, Boulevard Henri-Bourassa"},
    # "multiple results": {"street_number_and_name": "430 4e rue"}, # Enable this test case to test the error handling for multiple results
    "multiple results with unique id": {
        "street_number_and_name": "430 4e rue",
        "unique_id": "219232-134009"
    },
}

# French collection type to icon mapping
ICON_MAP = {
    "Ordures et résidus alimentaires": "mdi:trash-can",
    "Recyclage": "mdi:recycle",
    "Feuilles": "mdi:leaf",
}

# French to English collection type mapping
TYPE_MAP = {
    "Ordures et résidus alimentaires": "Garbage and Food Waste",
    "Recyclage": "Recycling",
    "Feuilles": "Leaves",
}

# French month names mapping
MONTH_NAMES = {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need to provide your street number and name in Quebec City.",
    "fr": "Vous devez fournir votre numéro et nom de rue dans la ville de Québec."
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_number_and_name": "Your street number and name in Quebec City (e.g. '123 Rue Example')",
        "unique_id": "(Optional) If multiple addresses match your search, this value is used to select one of them"
    },
    "fr": {
        "street_number_and_name": "Votre numéro et nom de rue dans la ville de Québec (ex. '123 Rue Example')",
        "unique_id": "(Optionnel) Si plusieurs adresses correspondent à votre recherche, cette valeur est utilisée pour en sélectionner une"
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street_number_and_name": "Street Number and Name",
        "unique_id": "Address Unique ID"
    },
    "fr": {
        "street_number_and_name": "Numéro et nom de rue",
        "unique_id": "ID unique d'adresse"
    }
}

#### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, street_number_and_name: str, unique_id: str = None):
        self._street_number_and_name = street_number_and_name
        self._unique_id = unique_id

    def fetch(self) -> list[Collection]:
        # Step 1: Initialize a session for maintaining cookies
        session = requests.Session()

        # Step 2: Get the initial page to extract form parameters
        response = session.get(URL)
        if response.status_code != 200:
            raise Exception(
                f"Failed to access {URL}, status code: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract required form fields
        viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value']
        eventvalidation = soup.find(
            'input', {'id': '__EVENTVALIDATION'})['value']
        viewstategenerator = soup.find(
            'input', {'id': '__VIEWSTATEGENERATOR'})['value']

        # Step 3: Prepare the form data for address search
        form_data = {
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstategenerator,
            '__EVENTVALIDATION': eventvalidation,
            'ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$txtNomRue': self._street_number_and_name,
            'ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$BtnRue': 'Rechercher',
        }

        # Step 4: Submit the search form
        search_response = session.post(URL, data=form_data)
        if search_response.status_code != 200:
            raise Exception(
                f"Failed to submit search request, status code: {search_response.status_code}")

        # Step 5: Parse the results page
        result_soup = BeautifulSoup(search_response.text, 'html.parser')

        # Check for errors or no results
        error_msg = result_soup.find('span', {
                                     'id': 'ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_lblErr'})
        if error_msg and error_msg.text.strip():
            raise SourceArgumentNotFound(
                argument='street_number_and_name',
                value=self._street_number_and_name,
                message_addition=f"Error searching for address: {error_msg.text.strip()}")

        # Check if multiple addresses match the search
        multiple_results_div = result_soup.find(
            'div', {'id': 'ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_RechercheAdresse_divPlusieursResultats'})
        if multiple_results_div:
            # Extract the available options from the dropdown
            address_select = result_soup.find('select', {
                                              'id': 'ctl00_ctl00_contenu_texte_page_ucInfoCollecteRechercheAdresse_RechercheAdresse_ddChoix'})
            if address_select:
                options = address_select.find_all('option')

                # Format addresses with their option values
                formatted_addresses = []
                option_values = {}
                for option in options:
                    address_text = option.text.strip()
                    option_value = option['value']
                    formatted_address = f"{address_text}. Use unique_id: {option_value}"
                    formatted_addresses.append(formatted_address)
                    option_values[option_value] = address_text

                # If unique_id is provided, use it to select the proper option
                if self._unique_id and self._unique_id in option_values:
                    # Submit form with the selected address
                    form_data = {
                        '__VIEWSTATE': result_soup.find('input', {'id': '__VIEWSTATE'})['value'],
                        '__VIEWSTATEGENERATOR': result_soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
                        '__EVENTVALIDATION': result_soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
                        'ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$ddChoix': self._unique_id,
                        'ctl00$ctl00$contenu$texte_page$ucInfoCollecteRechercheAdresse$RechercheAdresse$btnChoix': 'Poursuivre'
                    }
                    search_response = session.post(URL, data=form_data)
                    if search_response.status_code != 200:
                        raise Exception(
                            f"Failed to submit address selection, status code: {search_response.status_code}")

                    result_soup = BeautifulSoup(
                        search_response.text, 'html.parser')
                else:
                    # Raise the SourceArgAmbiguousWithSuggestions exception with formatted addresses
                    raise SourceArgAmbiguousWithSuggestions(
                        argument="street_number_and_name",
                        value=self._street_number_and_name,
                        suggestions=formatted_addresses,
                    )

        entries = []  # List that holds collection schedule

        # Find all calendar tables - these contain the collection dates
        calendar_tables = result_soup.find_all(
            'table', {'class': 'calendrier'})

        if not calendar_tables:
            raise SourceArgumentNotFound(
                argument='street_number_and_name',
                value=self._street_number_and_name,
                message_addition=f"No collection schedule available")

        # Parse each calendar to extract collection dates
        for table in calendar_tables:
            # Get month and year from caption
            caption = table.find('caption')
            if not caption:
                continue

            month_year = caption.text.strip()
            try:
                # Extract month and year using regex
                match = re.search(r'([A-Za-zÀ-ÿ]+)\s+(\d{4})', month_year)
                if match:
                    month_name = match.group(1).lower()
                    year = int(match.group(2))
                    month = MONTH_NAMES.get(month_name)

                    if not month:
                        continue

                    # Get all table rows (skip header row)
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for row in rows:
                        cells = row.find_all('td')

                        for cell in cells:
                            # Check if cell has a date
                            date_element = cell.find('p', {'class': 'date'})
                            if date_element and date_element.text.strip().isdigit():
                                day = int(date_element.text.strip())

                                # Check if cell has collection icons
                                img_container = cell.find(
                                    'p', {'class': 'img'})
                                if img_container:
                                    images = img_container.find_all('img')

                                    for img in images:
                                        french_collection_type = img.get(
                                            'title', img.get('alt', '')).strip()

                                        if french_collection_type:
                                            # Map French collection type to English
                                            english_collection_type = TYPE_MAP.get(
                                                french_collection_type, french_collection_type)

                                            # Create a date object
                                            try:
                                                collection_date = datetime.date(
                                                    year, month, day)

                                                # Add to entries list with English type and appropriate icon
                                                entries.append(
                                                    Collection(
                                                        date=collection_date,
                                                        t=english_collection_type,
                                                        icon=ICON_MAP.get(
                                                            french_collection_type)
                                                    )
                                                )
                                            except ValueError:
                                                # Skip invalid dates
                                                pass
            except Exception:
                # Skip this calendar if parsing fails
                continue

        return entries
