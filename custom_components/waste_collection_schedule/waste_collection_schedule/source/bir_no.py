import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "BIR (Bergensområdets Interkommunale Renovasjonsselskap)"
DESCRIPTION = "Askøy, Bergen, Bjørnafjorden, Eidfjord, Kvam, Osterøy, Samnanger, Ulvik, Vaksdal, Øygarden og Voss Kommune (Norway)."
URL = "https://bir.no"

TEST_CASES = {
    "Villa Paradiso": {
        "street_name": "Nordåsgrenda",
        "house_number": 7,
        "house_letter": "",
    },
    "Mardalsrenen 12 B": {
        "street_name": "Mardalsrenen",
        "house_number": "11",
    },
    "Alf Bondes Veg 13 B": {
        "street_name": "Alf Bondes Veg",
        "house_number": "13",
        "house_letter": "B",
    },
}

API_URL = "https://bir.no/api/search/AddressSearch"
ICON_MAP = {
    "restavfall": "mdi:trash-can",
    "papir": "mdi:newspaper-variant-multiple",
    "matavfall": "mdi:compost",
}


def map_icon(text):
    for key, value in ICON_MAP.items():
        if key in text:
            return value
    return "mdi:trash-can"


class Source:
    def __init__(self, street_name, house_number, house_letter=""):
        self._street_name = street_name
        self._house_number = house_number
        self._house_letter = house_letter

    def fetch(self):
        headers = {"user-agent": "Home-Assitant-waste-col-sched/0.1"}

        args = {
            "q": f"{self._street_name} {self._house_number}{self._house_letter} ",  # The space at the end is serving as a termination character for the query
            "s": False,
        }

        r = requests.get(API_URL, params=args, headers=headers)
        r = requests.get(
            f"{URL}/adressesoek/toemmekalender",
            params={"rId": {r.json()[0]["Id"]}},
            headers=headers,
        )
        doc = BeautifulSoup(r.content, "html.parser")
        month_containers = doc.select(
            ".main-content .address-page-box .month-container"
        )

        return [
            Collection(
                date=datetime.datetime.strptime(
                    f"{date.text.replace('des', 'dec').replace('mai', 'may').replace('okt', 'oct')} {container.select('.month-title')[0].text.strip().split(' ')[1]}",
                    "%d. %b %Y",
                ).date(),
                t=doc.select(
                    f'.trash-categories > .trash-row > img[src="{category_row.select(".icon > img")[0].get("src")}"] + .trash-text'
                )[0].text,
                icon=map_icon(
                    doc.select(
                        f'.trash-categories > .trash-row > img[src="{category_row.select(".icon > img")[0].get("src")}"] + .trash-text'
                    )[0].text.lower()
                ),
            )
            for container in month_containers
            for category_row in container.select(".category-row")
            for date in category_row.select(".date-item > .date-item-date")
        ]
