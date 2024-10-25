# import datetime
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Carmarthenshire County Council"
DESCRIPTION = "Source script for carmarthenshire.gov.wales"
URL = "https://www.carmarthenshire.gov.wales/"
COUNTRY = "uk"

TEST_CASES = {
    "Test_1": {"uprn": 10009546468},
    "Test_2": {"uprn": "100100146591"},
    "Test_3": {
        "uprn": 10004876405,
    },
}

ICON_MAP = {
    "BLUE": "mdi:recycle",
    "BLACK": "mdi:trash-can",
    "GARDEN": "mdi:leaf",
    "NAPPY": "mdi:biohazard",
}
REMAP_WASTE = {  # Map websire containers to underlying waste types
    "BLUE": "BLUE BAG & GREEN FOOD BIN",
    "BLACK": "BLACK BAG & GLASS BOX",
    "GARDEN": "GARDEN WATE",
    "NAPPY": "NAPPY & HYGIENE WASTE",
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
            f"https://www.carmarthenshire.gov.wales/umbraco/Surface/SurfaceRecycling/Index/?uprn={self._uprn}&lang=en-GB"
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        containers = soup.findAll("div", {"class": "bin-day-container"})
        entries = []
        for item in containers:
            dates = item.findAll("p", {"class": "font11 text-center"})
            entries.append(
                Collection(
                    date=datetime.strptime(
                        dates[0].text.split("  ")[1].strip(), "%d/%m/%Y"
                    ).date(),
                    t=REMAP_WASTE.get(item["class"][1].upper()),
                    icon=ICON_MAP.get(item["class"][1].upper()),
                )
            )

        return entries
