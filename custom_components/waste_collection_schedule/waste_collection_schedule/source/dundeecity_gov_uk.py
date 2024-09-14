# import datetime
from datetime import datetime

import json
import requests

from waste_collection_schedule import Collection

TITLE = "Dundee City Council"
DESCRIPTION = "Source script for dundeecity.gov.uk"
URL = "https://www.dundeecity.gov.uk"
EXTRA_INFO = [
    {"url": "https://www.dundee-mybins.co.uk"},
]
TEST_CASES = {
    "Test_1": {"uprn": 9059046613},
    "Test_2": {"uprn": "9059082280"},
    "Test_3": {
        "uprn": 9059060343,
    },
}
ICON_MAP = {
    "GREY BIN": "mdi:trash-can",
    "BROWN BIN": "mdi:leaf",
    "GREEN BIN": "mdi:bottle-wine",
    "BURGUNDY BIN": "mdi:recycle",
    "BLUE BIN": "mdi:newspaper",
}


# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering in your address details.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "uprn": "Every UK residential property is allocated a Unique Property Reference Number (UPRN). You can find yours by going to https://www.findmyaddress.co.uk/ and entering in your address details.",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "uprn": "Unique Property Reference Number",
    },
}

# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(
        self, uprn: str | int
    ):  # argX correspond to the args dict in the source configuration
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        response = s.get(
            f"https://www.dundee-mybins.co.uk/get_calendar.php?rn={self._uprn}"
        )
        response.raise_for_status()
        schedule = json.loads(response.text)

        entries = []

        for item in schedule:
            entries.append(
                Collection(
                    date=datetime.strptime(item["start"], "%Y-%M-%d").date(),
                    t=item["title"],
                    icon=ICON_MAP.get(item["title"].upper()),
                )
            )

        return entries
