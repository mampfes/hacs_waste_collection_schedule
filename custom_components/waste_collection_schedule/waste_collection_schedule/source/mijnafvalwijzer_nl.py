import datetime
import re

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Afval Wijzer"
DESCRIPTION = "Source for all cities regions supported in mijnafvalwijzer.nl"
URL = "https://www.mijnafvalwijzer.nl"
TEST_CASES = {
    "Eindhoven1": {"postcode": "5651AN", "number": "34", "add": "A"},
    "Eindhoven2": {"postcode": "5651AN", "number": "34"},
    "Tilburg": {"postcode": "5014NN", "number": "174"},
    "Meierijstad": {"postcode": "5481LR", "number": "6"},
    "Rotterdam": {"postcode": "3067AL", "number": "53"},
}

ICON_MAP = {  # Optional: Dict of waste types and suitable mdi icons
    "Restafval": "mdi:trash-can",
    "Papier en karton": "mdi:paper-roll",
    "Groente, Fruit en Tuinafval": "mdi:leaf",
    "PMD": "mdi:bottle-soda-classic-outline",
    "Plastic, Metalen en Drankkartons": "mdi:bottle-soda-classic-outline",
    "papier": "mdi:paper-roll",
    "GFT": "mdi:leaf",
    "GFT ": "mdi:leaf",
    "restafval": "mdi:trash-can",
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "INPUT ARGUMENTS ARE THE SAME AS THE ONES YOU FILL IN FOR YOUR HOME ADDRESS AT: https://www.mijnafvalwijzer.nl/",
}

# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, postcode, number, add=""):
        self._postcode = postcode
        self._number = number
        if add is None:
            self._add = ""
        else:
            self._add = add

    def fetch(self):
        s = requests.Session()

        r = s.get(
            URL
            + "/nl/"
            + self._postcode.replace(" ", "")
            + "/"
            + self._number.replace(" ", "")
            + "/"
            + self._add.replace(" ", "")
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        soup = soup.find("div", id="jaaroverzicht", class_="pageBlock")
        years = soup.find_all("div", id=re.compile("^jaar-"), class_="ophaaldagen")

        dict_month = {
            "januari": 1,
            "februari": 2,
            "maart": 3,
            "april": 4,
            "mei": 5,
            "juni": 6,
            "juli": 7,
            "augustus": 8,
            "september": 9,
            "oktober": 10,
            "november": 11,
            "december": 12,
        }

        date_day = []
        date_month = []
        date_year = []
        types_list = []
        for year in years:
            year_int = int(year.get("id")[-4:])
            dates = soup.find_all("span", class_="span-line-break")
            for date in dates:
                date_day.append(int(date.string.split()[1]))
                date_month.append(dict_month[date.string.split()[2]])
                date_year.append(year_int)
            types = soup.find_all("span", class_="afvaldescr")
            for type in types:
                types_list.append(type.string)

        entries: list[Collection] = []

        for day, month, year, bin_type in zip(
            date_day, date_month, date_year, types_list
        ):
            try:
                entries.append(
                    Collection(
                        date=datetime.date(year, month, day),  # Collection date
                        t=bin_type,  # Collection type
                        icon=ICON_MAP.get(bin_type),  # Collection icon
                    )
                )
            except Exception:
                pass

        return entries
