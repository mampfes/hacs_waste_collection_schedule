import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Canning (WA)"
DESCRIPTION = "Source for City of Canning, Western Australia"
URL = "https://www.canning.wa.gov.au"
TEST_CASES = {
    "Test_001": {"address": "1325 Albany Highway CANNINGTON  6107"},
    "Test_002": {"address": "3 Rossmoyne Drive ROSSMOYNE  6148"},
    "Test_003": {"address": "12 Battersea Road CANNING VALE  6155"},
}
HEADERS = {"User-Agent": "Mozilla/5.0"}
ICON_MAP = {
    "Rubbish": "trash-can",
    "Recycling": "mdi:recycle",
    "Green": "mdi:leaf",
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Your address, as it is displayed on the website when showing your collection schedule. Note: There are usually two whitespace characters between the suburb and postal code.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "address": "Your address, as it is displayed on the website when showing your collection schedule. Note: There are usually two whitespace characters between the suburb and postal code.",
    },
}


class Source:
    def __init__(self, address: str):

        self._address = address

    def fetch(self):

        s = requests.session()

        # get property key(s), assume first one is correct, then get schedule
        r = s.get(
            f"https://www.canning.wa.gov.au/api/property-details/find/{self._address}",
            headers=HEADERS,
        )
        data = json.loads(r.content.decode("utf-8"))
        address_key = data[0]["key"]
        r = s.get(
            f"https://www.canning.wa.gov.au/api/property-details/bins/{address_key}",
            headers=HEADERS,
        )
        schedule = json.loads(r.content.decode("utf-8"))

        # response is a mix of lists, empty lists, and strings
        entries = []
        for item in schedule:
            waste_type = item.split("Collection")[0].split("Waste")[0].capitalize()
            if isinstance(schedule[item], list):
                try:
                    waste_date = schedule[item][0]
                except IndexError:
                    continue
            elif isinstance(schedule[item], str):
                waste_date = schedule[item]
            entries.append(
                Collection(
                    date=datetime.strptime(waste_date, "%Y-%m-%dT%H:%M:%S%z").date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries
