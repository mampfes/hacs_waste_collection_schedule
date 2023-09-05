import json
import requests
import datetime

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "FKF Budaörs"
DESCRIPTION = "Source script for www.fkf.hu"
URL = "https://www.fkf.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_1": {"street": "Templom tér"},
    "Test_2": {"street": "Völgy utca"},
    "Test_3": {"street": "Zombori utca"}
}

API_URL = "https://www.fkf.hu/hulladeknaptar-budaors"
ICON_MAP = {
    "COMMUNAL": "mdi:trash-can",
    "SELECTIVE": "mdi:recycle",
    "GREEN": "mdi:leaf",
}


class Source:
    def __init__(self, street):
        self._street = street

    def fetch(self):
        session = requests.Session()

        r = session.post(
            API_URL,
            data={
                "publicPlace": self._street
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-October-Request-Handler": "onSearch",
                "X-October-Request-Partials": "ajax/budaorsResults",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        r.raise_for_status()
        soup = BeautifulSoup(json.loads(r.text)["ajax/budaorsResults"], features="html.parser")

        if soup.find("div", attrs={"class":"alert"}) is not None:
            raise Exception("Address not found")

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
