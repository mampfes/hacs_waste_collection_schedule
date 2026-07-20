import datetime
from waste_collection_schedule import Collection, Icons

TITLE = "S.E.S.A."
DESCRIPTION = "Source script for sesaeste.it"
URL = "https://sesaeste.it/"
TEST_CASES = {
    "TestName1": {"arg1": 100, "arg2": "street"},
    "TestName2": {"arg1": 200, "arg2": "road"},
    "TestName3": {"arg1": 300, "arg2": "lane"}
}

API_URL = "https://sesaeste.it/proc_cerca_comune/"
ICON_MAP = {   # Optional: Dict of waste types mapped to canonical Icons
    "DOMESTIC": Icons.GENERAL_WASTE,
    "RECYCLE": Icons.RECYCLING,
    "ORGANIC": Icons.ORGANIC,
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields.
    # Only "en", "de", "it", "fr" are valid keys — other codes (e.g. "pl", "nl") will fail the test suite.
    # You do NOT need to provide all four languages; providing only the language(s) you know is fine.
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
    "fr": "COMMENT OBTENIR LES ARGUMENTS",
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
    "fr": {
        "arg1": "Description de ARG1",
        "arg2": "Description de ARG2",
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
    "fr": {
        "arg1": "Nom lisible par l'utilisateur pour ARG1",
        "arg2": "Nom lisible par l'utilisateur pour ARG2",
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, arg1:str, arg2:int):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
        self._arg2 = arg2

    def fetch(self) -> list[Collection]:

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        if ERROR_CONDITION:
            raise Exception("YOUR ERROR MESSAGE HERE") # DO NOT JUST return []

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.datetime(2020, 4, 11),  # Collection date
                t = "Waste Type",  # Collection type
                icon = ICON_MAP.get("Waste Type"),  # Collection icon
            )
        )

        return entries