import re
import datetime
import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Eindhoven"
DESCRIPTION = "Source for Eindhoven"
URL = "https://www.mijnafvalwijzer.nl"
TEST_CASES = {
    "Eindhoven1": {"postcode": "5651AN", "number": "34", "add": "A"},
    "Eindhoven2": {"postcode": "5651AN", "number": "34"},
    "Tilburg": {"postcode": "5014NN", "number": "174"},
    "Meierijstad": {"postcode": "5481LR", "number": "6"},
}

ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
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

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "postcode": "Postcode",
        "number": "House number",
        "add": "Addition"
    },
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "postcode": "Postcode",
        "number": "House number",
        "add": "Addition"
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, postcode, number, add=""):
        self._postcode = postcode
        self._number = number
        self._add = add

    def fetch(self):
        s = requests.Session()

        r = s.get(URL + '/nl/' + self._postcode.replace(" ","") + '/' + self._number.replace(" ","") + '/' + self._add.replace(" ",""))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        soup = soup.find('div', id= 'jaaroverzicht', class_ = 'pageBlock')
        years = soup.find_all('div', id = re.compile('^jaar-'), class_ = 'ophaaldagen')

        dict_month = {"januari":1,
                    "februari":2,
                    "maart":3,
                    "april":4,
                    "mei":5,
                    "juni":6,
                    "juli":7,
                    "augustus":8,
                    "september":9,
                    "oktober":10,
                    "november":11,
                    "december":12
                }
        
        date_day = []
        date_month = []
        date_year =[]
        types_list = []
        for year in years:
            year_int = int(year.get('id')[-4:])
            print(year_int)
            dates = soup.find_all('span', class_='span-line-break')
            for date in dates:
                date_day.append(int(date.string.split()[1]))
                date_month.append(dict_month[date.string.split()[2]])
                date_year.append(year_int)
            types = soup.find_all('span', class_='afvaldescr')
            for type in types:
                types_list.append(type.string)        
        
        

        #entries = []  # List that holds collection schedule
        entries: list[Collection] = []

        ii=0
        while ii < len(date_day):
            try:
                entries.append(
                    Collection(
                        date = datetime.date(date_year[ii], date_month[ii], date_day[ii]),  # Collection date
                        t = types_list[ii],  # Collection type
                        icon = ICON_MAP.get(types_list[ii]),  # Collection icon
                    )
                )
            except:
                pass
#                raise Exception("Error in date: " + str(date_year[ii]) + "-" + str(date_month[ii]) + "-" + str(date_day[ii]))
            ii = ii+1
        
        return entries
