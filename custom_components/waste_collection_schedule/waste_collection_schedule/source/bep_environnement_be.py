from datetime import date
from typing import List
import requests
from bs4 import BeautifulSoup
import json
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule import Collection

TITLE = "Bep-Environnement"
DESCRIPTION = "Source for Bep Environnement garbage collection"  # Describe your source
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://www.bep-environnement.be"
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Dinant": {"locality": "Dinant"},
}

WASTE_MAP = {
    # Déchers ménagers + organique
    "dmorga": {"type": "DM & Organiques", "icon": "mdi:trash-can"},
    # PMC
    "pmc": {"type": "PMC", "icon": "mdi:recycle"},
    # Papiers cartons
    "papierscartons": {"type": "Papiers & Cartons", "icon": "mdi:leaf"}
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "locality": "Name of the locality"
    }
}


def GetCitiesValue() -> List[dict]:
    """Return id for each city available in calendar

    Returns:
        List[dict]: key is the city, value is the id for the calendar
    """
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all <option> elements inside the select
    options = soup.select('#locform-loc option')

    # Create a dictionary of city names and their values
    city_values = {option.text.lower(): option['value']
                   for option in options if option.text.strip()}

    # Print the result
    return city_values


def BepWasteParser(response: dict) -> List[Collection]:
    """Specific implementation to parse response from Bep-Environement

    Args:
        response (dict): response from the website

    Returns:
        List[Collection]: list of Collection found
    """
    collections = []
    cal_soup = BeautifulSoup(response.get("cal", ""), "html.parser")
    cells = cal_soup.find_all("td")

    for cell in cells:
        # Extract attributes
        data_day = cell.get("data-day")
        data_month = cell.get("data-month")
        data_year = cell.get("data-year")

        # Check for waste types in the class attribute
        classes = cell.get("class", [])
        waste_types = [cls for cls in classes if cls in WASTE_MAP]

        if data_day and data_month and data_year and waste_types:
            # Construct the date
            collection_date = date(
                year=int(data_year), month=int(data_month), day=int(data_day)
            )

            for abbr, map in WASTE_MAP.items():
                if abbr in waste_types:
                    c = Collection(date=collection_date,
                                   t=map["type"], icon=map["icon"])
                    collections.append(c)

    return collections


class Source:
    BEP_CALENDAR_URL = "https://www.bep-environnement.be/wp-admin/admin-ajax.php"
    GARBAGE_COLLECTION_ACTION = "calendriercollectes"

    def __init__(self, locality: str):
        self._locality = locality.lower()

    def fetch(self) -> list[Collection]:
        # Check for city name given
        citiesValue = GetCitiesValue()

        if self._locality not in citiesValue:
            raise SourceArgumentException(
                "locality", f"{self._locality} does not exist in the BEP website")

        # Make the request to get the data
        params = {
            "action": self.GARBAGE_COLLECTION_ACTION,
            "locID": citiesValue[self._locality]
        }
        response = requests.get(
            self.BEP_CALENDAR_URL, params=params
        )
        response.raise_for_status()
        data = json.loads(response.text)

        # Parse the response
        entries = BepWasteParser(data)

        return entries
