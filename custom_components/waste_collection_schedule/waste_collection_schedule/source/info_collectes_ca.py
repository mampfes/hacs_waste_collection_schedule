from datetime import datetime
from waste_collection_schedule import Collection
import requests
import unicodedata

TITLE = "MRC de Roussillon (QC, Canada)" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for info-collectes.ca/"  # Describe your source
URL = "https://info-collectes.ca/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestName1": {"arg1": 'La Prairie'},
    "TestName2": {"arg1": "candiac", "arg2": "est"},
    "TestName3": {"arg1": "chateauguay", "arg2": "est"},
    "TestName4": {"arg1": "chateauguay", "arg2": "sud"},
    "TestName5": {"arg1": 'lery'},
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

CITY_NAMES = ["candiac",
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
    def __init__(self, arg1:str, arg2:str=None):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
        if arg2:
            self._arg2 = arg2.lower()
        else:
            self._arg2 = None

    def fetch(self) -> list[Collection]:

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        city = _normalize_city_name(self._arg1)
        if city not in CITY_NAMES:
            raise Exception("Invalid City Name.")

        if self._arg2:
            if city != 'chateauguay':
                raise Exception(f"Invalid sector for {city.capitalize()}")
            if self._arg2 not in ['nord-ouest', "est"]:
                raise Exception(f"Invalid sector for {city.capitalize()}, available sector: nord-ouest, est")
            city = city + "-"  + "secteur" + "-" + self._arg2
        
        data = {
            "action": "ajaxJsYearCalendar",
            "region": city,
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