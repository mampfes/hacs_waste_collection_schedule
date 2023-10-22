import datetime
import json

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "ÉTH (Érd, Diósd, Nagytarcsa, Sóskút, Tárnok)"
DESCRIPTION = "Source script for www.eth-erd.hu"
URL = "https://www.eth-erd.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_1": {"city": "Diósd", "street": "Diófasor", "house_number": 10},
    "Test_2": {"city": "Érd", "street": "Hordó", "house_number": 3},
    "Test_3": {"city": "Sóskút"},
}

API_URL = "https://www.eth-erd.hu/trashcalendarget"

ICON_MAP = {
    "Kommunális": "mdi:trash-can",
    "Szelektív": "mdi:recycle",
    "Zöldhulladék": "mdi:leaf",
    "Papír": "mdi:newspaper",
    "Fenyőfa": "mdi:pine-tree",
    "Üveg": "mdi:glass-fragile",
}

NAME_MAP = {
    "Kommunális": "Communal",
    "Szelektív": "Selective",
    "Zöldhulladék": "Green",
    "Papír": "Paper",
    "Fenyőfa": "Pine Tree",
    "Üveg": "Glass",
}

CITY_MAP = {
    "diósd": 1,
    "érd": 2,
    "nagytarcsa": 822,
    "sóskút": 3,
    "tárnok": 4,
}


class Source:
    def __init__(self, city: str, street: str = "", house_number: int = 1) -> None:
        self._city = city
        self._street = street
        self._house_number = house_number

    def fetch(self):
        session = requests.Session()

        city_id = CITY_MAP.get(self._city.lower())
        if city_id is None:
            raise Exception("City not found")
        has_streets = city_id != CITY_MAP["sóskút"]

        if has_streets:
            r = session.post(
                API_URL + "streets",
                data={"sid": city_id},
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                },
            )
            r.raise_for_status()
            streets = json.loads(r.text)["results"]
            available_streets = [item["text"] for item in streets]
            try:
                street_id = [
                    item for item in streets if item.get("text") == self._street
                ][0]["id"]
            except IndexError:
                raise Exception(
                    "Street not found, available streets: "
                    + ", ".join(available_streets)
                )

        r = session.post(
            API_URL,
            data={
                "wctown": city_id,
                "wcstreet": street_id,
                "wchousenumber": self._house_number,
            }
            if has_streets
            else {
                "wctown": city_id,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        r.raise_for_status()
        result: dict = json.loads(r.text)

        entries = []

        for trash_type_id in result["types"]:
            trash_type = result["types"][trash_type_id]
            trash_icon = ICON_MAP[trash_type["name"]]
            trash_name = NAME_MAP[trash_type["name"]]

            for element in result["routelist"][trash_type_id]:
                entries.append(
                    Collection(
                        date=datetime.datetime.strptime(element, "%Y-%m-%d").date(),
                        t=trash_name,
                        icon=trash_icon,
                    )
                )

        return entries
