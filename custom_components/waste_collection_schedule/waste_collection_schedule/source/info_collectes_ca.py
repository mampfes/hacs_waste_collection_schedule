from datetime import datetime
from waste_collection_schedule.exceptions import SourceArgumentException, SourceArgumentNotFound
from waste_collection_schedule import Collection
import requests
import unicodedata

TITLE = "MRC de Roussillon (QC, Canada)" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for info-collectes.ca/"  # Describe your source
URL = "https://info-collectes.ca/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestName1": {"city": 'La Prairie'},
    "TestName2": {"city": "candiac", "sector": "est"},
    "TestName3": {"city": "chateauguay", "sector": "est"},
    "TestName4": {"city": "chateauguay", "sector": "sud"},
    "TestName5": {"city": 'lery'},
}

API_URL = "https://info-collectes.ca/wp/wp-admin/admin-ajax.php"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "organic": "mdi:compost",
    "recycling": "mdi:recycle",
    "greenWaste": "mdi:leaf",
    "cardboard": "mdi:package-variant",
    "bulky": "mdi:sofa",
    "garbage": "mdi:truck-remove"
}

MUNICIPALITY_NAMES = ["candiac",
                      "saint-constant",
                      "chateauguay",
                      "saint-isidore",
                      "delson",
                      "saint-mathieu",
                      "la-prairie",
                      "saint-philippe",
                      "lery",
                      "sainte-catherine",
                      "mercier",]

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "fr": "COMMENT OBTENIR LES ARGUMENTS",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "arg1": "City Name",
        "arg2": "Sector",
    },
    "fr": {
        "arg1": "Nom de la ville",
        "arg2": "Secteur",
    },
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "arg1": "City name in MRC de Roussillon",
        "arg2": "Optional, Sector for Châteauguay, nord-ouest or est",
    },
    "fr": {
        "arg1": "Nom de la ville dans le MRC de Roussillon",
        "arg2": "En option, Secteur de Châteauguay, nord-ouest ou est",
    },
}

#### End of arguments affecting the configuration GUI ####
def _normalize_city_name(city_name):
    t = unicodedata.normalize("NFKD", city_name)
    normalized__name = "".join(s for s in t if not unicodedata.combining(s))
    return normalized__name.replace(' ', '-').lower()


class Source:
    def __init__(self, municipality:str, sector:str=None):  # argX correspond to the args dict in the source configuration
        self.municipality = municipality
        if sector:
            self.sector = sector.lower()
        else:
            self.sector = None

    def fetch(self) -> list[Collection]:

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        municipality_name = _normalize_city_name(self.municipality)
        if not municipality_name:
            raise SourceArgumentNotFound("municipality", self.municipality, "Empty municipality name.")
        if municipality_name not in MUNICIPALITY_NAMES:
            raise SourceArgumentException("municipality", f"Invalid municipality name: {self.municipality}.")

        if self.sector:
            if municipality_name != 'chateauguay':
                raise SourceArgumentException(self.sector, f"Invalid sector for {municipality_name.capitalize()}")
            if self.sector not in ['nord-ouest', "est"]:
                raise SourceArgumentException(self.sector, f"Invalid sector for {municipality_name.capitalize()}, available sector: nord-ouest, est")
            municipality_name = municipality_name + "-"  + "secteur" + "-" + self.sector
        
        data = {
            "action": "ajaxJsYearCalendar",
            "region": municipality_name,
            }

        resp = requests.post(API_URL, data=data)
        resp.raise_for_status()
        cal = resp.json()["data"]

        if not cal:
            raise Exception("Failed to get collection schedule") # DO NOT JUST return []
        
        entries = []  # List that holds collection schedule

        for day in cal:
            entries.append(
                Collection(
                    date = datetime.strptime(day['date'], "%Y%m%d").date(),  # Collection date
                    t = day['icone'][0],  # Collection type
                    icon = ICON_MAP.get(day['icone'][0]),  # Collection icon
                )
            )

        return entries