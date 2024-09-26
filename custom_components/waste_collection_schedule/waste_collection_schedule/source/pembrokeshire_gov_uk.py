import datetime
from waste_collection_schedule import Collection
import requests
from datetime import datetime

TITLE = "Pembrokeshire County Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for pembrokeshire.gov.uk"  # Describe your source
URL = "https://www.pembrokeshire.gov.uk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Picton Road": {"uprn": "100100291142"},
}

API_URL = "https://www.pembrokeshire.gov.uk/template/waste/api.asp"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "FOODCAD": "mdi:trash-can",
    "BLUEBOX": "mdi:recycle",
    "GREENBOX": "mdi:leaf",
    "BLUEBAG": "mdi:trash-can",
    "REDBAG": "mdi:trash-can",
    "GREYBAG": "mdi:trash-can",
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "arg1": "Description of ARG1",
        "arg2": "Description of ARG2",
    },
    "de": {
        "arg1": "Beschreibung von ARG1",
        "arg2": "Beschreibung von ARG2",
    },
    "it": {
        "arg1": "Descrizione di ARG1",
        "arg2": "Descrizione di ARG2",
    },
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "arg1": "User Readable Name for ARG1",
        "arg2": "User Readable Name for ARG2",
    },
    "de": {
        "arg1": "Benutzerfreundlicher Name für ARG1",
        "arg2": "Benutzerfreundlicher Name für ARG2",
    },
    "it": {
        "arg1": "Nome leggibile dall'utente per ARG1",
        "arg2": "Nome leggibile dall'utente per ARG2",
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, uprn: str):  # argX correspond to the args dict in the source configuration
        self._uprn = uprn

    def fetch(self) -> list[Collection]:

        session = requests.Session()

        form_data = {
            "action":"dates",
            "public":"true",
            "uprn":self._uprn,
            "language":"eng",

        }

        collection_response = session.post(API_URL, params=form_data)
        
        if eval(collection_response.text)["error"] == "true":
            raise Exception("No collections found for the given UPRN.") # DO NOT JUST return []
        
        entries = []  # List that holds collection schedule

        bin_dates = eval(collection_response.text)["bins"]
        for bin in bin_dates:
            date_string = bin["nextdate"]
            date_format = "%d/%m/%Y"
            date = datetime.strptime(date_string, date_format).date()
            bin_type = bin["type"]

            entries.append(
            Collection(
                date = date,  # Collection date
                t = bin_type,  # Collection type
                icon = ICON_MAP.get(bin_type),  # Collection icon
            )
        )

        return entries