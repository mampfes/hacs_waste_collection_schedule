import json
import requests
import datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "FKF Budapest"
DESCRIPTION = "Source script for www.fkf.hu"
URL = "https://www.fkf.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_1": {
        "district": 1011,
        "street": "Apród utca",
        "house_number": 10
    },
    "Test_2": {
        "district": 1114,
        "street": "Szent Gellért tér",
        "house_number": 3
    },
    "Test_3": {
        "district": 1202,
        "street": "Bölön utca",
        "house_number": 5
    }
}

API_URL = "https://www.fkf.hu/hulladeknaptar"
ICON_MAP = {
    "COMMUNAL": "mdi:trash-can",
    "SELECTIVE": "mdi:recycle",
    "GREEN": "mdi:leaf",
}


class Source:
    def __init__(self, district, street, house_number):
        self._district = district
        self._street = street[::-1].replace(" ", "---", 1)[::-1]
        self._house_number = house_number

    def fetch(self):
        session = requests.Session()

        r = session.post(
            API_URL,
            data={
                "district": self._district
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSelectDistricts",
                "X-October-Request-Partials": "ajax/publicPlaces",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        r.raise_for_status()
        soup = BeautifulSoup(json.loads(r.text)["ajax/publicPlaces"], features="html.parser")

        if soup.find("div", attrs={"class":"alert"}) is not None:
            raise Exception("District not found")

        available_streets = []
        for opt in soup.find_all("option")[1:]:
            available_streets.append(opt.decode_contents())

        available_streets = ", ".join(available_streets)

        r = session.post(
            API_URL,
            data={
                "publicPlace": self._street
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSavePublicPlace",
                "X-October-Request-Partials": "ajax/houseNumbers",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        r.raise_for_status()
        soup = BeautifulSoup(json.loads(r.text)["ajax/houseNumbers"], features="html.parser")

        if soup.find("div", attrs={"class":"alert"}) is not None or soup.find("option", string="Kérem, előbb válasszon közterületet") is not None:
            raise Exception("Street not found, available streets: " + available_streets)

        available_numbers = []
        for opt in soup.find_all("option")[1:]:
            available_numbers.append(opt.decode_contents())

        available_numbers = ", ".join(available_numbers)

        r = session.post(
            API_URL,
            data={
                "houseNumber": self._house_number
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSearch",
                "X-October-Request-Partials": "ajax/calSearchResults",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        r.raise_for_status()
        soup = BeautifulSoup(json.loads(r.text)["ajax/calSearchResults"], features="html.parser")

        if soup.find("div", attrs={"class":"alert"}) is not None:
            raise Exception("House number not found, available house numbers: " + available_numbers)

        entries = []
        communal_divs = soup.find_all("div", attrs={"class":"communal"})

        selective = soup.find_all("div", attrs={"class":"selective"})
        communal = [i for i in filter(lambda div:div.text=="Kommunális", communal_divs)]
        green = [i for i in filter(lambda div:div.text=="Zöld", communal_divs)]

        for element in communal:
            entries.append(
                Collection(
                    date = datetime.datetime.strptime(element.parent.parent.findAll("td")[1].text, "%Y.%m.%d").date(),
                    t = "Communal",
                    icon = ICON_MAP.get("COMMUNAL"),
                )
            )

        for element in selective:
            entries.append(
                Collection(
                    date = datetime.datetime.strptime(element.parent.parent.findAll("td")[1].text, "%Y.%m.%d").date(),
                    t = "Selective",
                    icon = ICON_MAP.get("SELECTIVE"),
                )
            )

        for element in green:
            entries.append(
                Collection(
                    date = datetime.datetime.strptime(element.parent.parent.findAll("td")[1].text, "%Y.%m.%d").date(),
                    t = "Green",
                    icon = ICON_MAP.get("GREEN"),
                )
            )

        return entries
