import datetime
import json

import requests
import urllib3
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TITLE = "MOHU Budapest"
DESCRIPTION = "Source script for www.mohubudapest.hu"
URL = "https://www.mohubudapest.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_1": {"district": 1011, "street": "Apród utca", "house_number": 10},
    "Test_2": {"district": 1114, "street": "Szent Gellért tér", "house_number": 3},
    "Test_3": {"district": 1202, "street": "Bölön utca", "house_number": 5},
    "Test_4": {
        "district": 1011,
        "street": "Apród utca",
        "house_number": 10,
        "verify": False,
    },
    "Test_5": {
        "district": 1114,
        "street": "Szent Gellért tér",
        "house_number": 3,
        "verify": False,
    },
    "Test_6": {
        "district": 1202,
        "street": "Bölön utca",
        "house_number": 5,
        "verify": False,
    },
}

API_URL = "https://mohubudapest.hu/hulladeknaptar"
ICON_MAP = {
    "COMMUNAL": "mdi:trash-can",
    "SELECTIVE": "mdi:recycle",
    "GREEN": "mdi:leaf",
}


class Source:
    def __init__(self, district, street, house_number, verify=True):
        self._district = district
        self._street = street[::-1].replace(" ", "---", 1)[::-1]
        self._house_number = house_number
        self._verify = verify

    def fetch(self):
        session = requests.Session()

        r = session.post(
            API_URL,
            data={"district": self._district},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSelectDistricts",
                "X-October-Request-Partials": "ajax/publicPlaces",
                "X-Requested-With": "XMLHttpRequest",
            },
            verify=self._verify,
        )
        r.raise_for_status()
        soup = BeautifulSoup(
            json.loads(r.text)["ajax/publicPlaces"], features="html.parser"
        )

        if soup.find("div", attrs={"class": "alert"}) is not None:
            raise SourceArgumentNotFound("district")

        available_streets = []
        for opt in soup.find_all("option")[1:]:
            available_streets.append(opt.decode_contents())

        r = session.post(
            API_URL,
            data={"publicPlace": self._street},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSavePublicPlace",
                "X-October-Request-Partials": "ajax/houseNumbers",
                "X-Requested-With": "XMLHttpRequest",
            },
            verify=self._verify,
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            ) from e
        soup = BeautifulSoup(
            json.loads(r.text)["ajax/houseNumbers"], features="html.parser"
        )

        if (
            soup.find("div", attrs={"class": "alert"}) is not None
            or soup.find("option", string="Kérem, előbb válasszon közterületet")
            is not None
        ):
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )

        available_numbers = []
        for opt in soup.find_all("option")[1:]:
            available_numbers.append(opt.decode_contents())

        r = session.post(
            API_URL,
            data={"houseNumber": self._house_number},
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSearch",
                "X-October-Request-Partials": "ajax/calSearchResults",
                "X-Requested-With": "XMLHttpRequest",
            },
            verify=self._verify,
        )
        r.raise_for_status()
        soup = BeautifulSoup(
            json.loads(r.text)["ajax/calSearchResults"], features="html.parser"
        )

        if soup.find("div", attrs={"class": "alert"}) is not None:
            raise SourceArgumentNotFoundWithSuggestions(
                "house_number", self._house_number, available_numbers
            )

        entries = []
        communal_divs = soup.find_all("div", attrs={"class": "communal"})

        selective = soup.find_all("div", attrs={"class": "selective"})
        communal = [
            i for i in filter(lambda div: div.text == "Kommunális", communal_divs)
        ]
        green = [i for i in filter(lambda div: div.text == "Zöld", communal_divs)]

        for element in communal:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        element.parent.parent.findAll("td")[1].text, "%Y.%m.%d"
                    ).date(),
                    t="Communal",
                    icon=ICON_MAP.get("COMMUNAL"),
                )
            )

        for element in selective:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        element.parent.parent.findAll("td")[1].text, "%Y.%m.%d"
                    ).date(),
                    t="Selective",
                    icon=ICON_MAP.get("SELECTIVE"),
                )
            )

        for element in green:
            entries.append(
                Collection(
                    date=datetime.datetime.strptime(
                        element.parent.parent.findAll("td")[1].text, "%Y.%m.%d"
                    ).date(),
                    t="Green",
                    icon=ICON_MAP.get("GREEN"),
                )
            )

        return entries
