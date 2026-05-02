import json
from datetime import datetime

import requests
from waste_collection_schedule import Collection

TITLE = "Győri Hulladékgazdálkodási Nonprofit Kft."
DESCRIPTION = "Source script using GYHG API at https://gyhg.bluespot.hu/api"
URL = "https://www.gyhg.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_1": {"city": "Écs", "street": "Ady Endre utca", "house_number": "1/A"},
    "Test_2": {
        "city": "Mosonszentmiklós-Mosonújhely",
        "street": "Radnóti Miklós utca",
        "house_number": 25,
    },
    "Test_3": {"city": "Veszprémvarsány", "street": "Zrínyi utca", "house_number": 34},
}

API_URL = "https://gyhg.bluespot.hu/api/"

ICON_MAP = {
    "leftover": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "bio": "mdi:compost",
}

NAME_MAP = {
    "leftover": "Communal",
    "recycle": "Selective",
    "bio": "Green",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Select the desired address on the https://www.gyhg.hu/hulladeknaptar#/ website. The town, street name, and house number must be entered in this integration in the exact same format as they appear there.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "city": "City name",
        "street": "Street name",
        "house_number": "House number",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "city": "City name",
        "street": "Street name",
        "house_number": "House number",
    },
}

# End of arguments affecting the configuration GUI


class Source:
    def __init__(self, city: str, street: str, house_number: str | int):
        self._city = city
        self._street = street
        self._house_number = str(house_number)

    def fetch(self) -> list[Collection]:

        session = requests.Session()
        raw_json = session.get(
            API_URL + "get_schedule",
            params={
                "city_name": self._city,
                "street": self._street,
                "house_number": self._house_number,
            },
            timeout=10,
        )
        raw_json.raise_for_status()
        parsed_data = json.loads(raw_json.text)["data"]

        entries = []  # List that holds collection schedule

        for waste, date_list in parsed_data.items():
            if date_list:  # Filter out Null values
                for date_str in date_list:
                    entries.append(
                        Collection(
                            date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                            t=NAME_MAP.get(waste, waste),
                            icon=ICON_MAP.get(waste, "mdi:trash-can"),
                        )
                    )

        return entries
