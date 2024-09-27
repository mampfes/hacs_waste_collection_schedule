import datetime
from waste_collection_schedule import Collection
import requests
from datetime import datetime
import ast

TITLE = "Pembrokeshire County Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for pembrokeshire.gov.uk"  # Describe your source
URL = "https://www.pembrokeshire.gov.uk/"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Dew Street": {"uprn": "100100283349"},
    "Heol Cleddau": {"uprn": "100100281816"}
}

API_URL = "https://www.pembrokeshire.gov.uk/template/waste/api.asp"

TYPE_MAP = {   # Dict of waste formatted bin types
    "FOODCAD": "GREEN CADDY",
    "BLUEBOX": "BLUE BOX",
    "GREENBOX": "GREEN BOX",
    "BLUEBAG": "BLUE BAG",
    "REDBAG": "RED BAG",
    "GREYBAG": "BLACK/GREY BAGS",
}
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "FOODCAD": "mdi:food-apple",
    "BLUEBOX": "mdi:note-multiple",
    "GREENBOX": "mdi:glass-fragile",
    "BLUEBAG": "mdi:recycle",
    "REDBAG": "mdi:recycle",
    "GREYBAG": "mdi:trash-can",
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "To get your UPRN go to https://www.findmyaddress.co.uk and search for your address.",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
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
        
        if ast.literal_eval(collection_response.text)["error"] == "true":
            raise Exception("No collections found for the given UPRN.")
        
        entries = []  # List that holds collection schedule

        bin_dates = ast.literal_eval(collection_response.text)["bins"]
        for bin in bin_dates:
            date_string = bin["nextdate"]
            date_format = "%d/%m/%Y"
            date = datetime.strptime(date_string, date_format).date()
            bin_type = bin["type"]

            entries.append(
            Collection(
                date = date,  # Collection date
                t = TYPE_MAP.get(bin_type),  # Collection type
                icon = ICON_MAP.get(bin_type),  # Collection icon
            )
        )

        return entries