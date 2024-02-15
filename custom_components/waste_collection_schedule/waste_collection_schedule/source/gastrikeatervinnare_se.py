from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Gästrike Återvinnare"
DESCRIPTION = "Source for Gästrike Återvinnare waste collection"
URL = "https://gastrikeatervinnare.se/"
API_URL = "https://gastrikeatervinnare.se/wp-admin/admin-ajax.php"
TEST_CASES = {
    "Groceries Årsunda": {"street": "Nedre Vägen 52", "city": "Årsunda"},
    "Police Sandviken": {"street": "Bryggargatan 6", "city": "Sandviken"},
    "Police Gävle": {"street": "Södra Centralgatan 1", "city": "Gävle"},
    "Library Ockelbo": {"street": "Södra Åsgatan 30D", "city": "Ockelbo"},
}
ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:leaf",
    "Blandat": "mdi:trash-can",
}


class Source:
    def __init__(self, street, city):
        self._street = street.strip().lower()
        self._city = city.strip().lower()

    def fetch(self):
        data = {"action": "pickup_search", "query": self._street}
        response = requests.post(API_URL, data=data)
        response.encoding = "UTF-8"
        soup = BeautifulSoup(response.text, "html.parser")
        addresses = soup.find_all("p", attrs={"class": "pickup-adress"})
        infos = soup.find_all("div", attrs={"class": "pickup-types"})

        for addressTag, info in zip(addresses, infos):
            street = addressTag.text.split(",")[0].strip().lower()
            city = (
                addressTag.find("span", attrs={"class": "pickup-locality"})
                .text.strip()
                .lower()
            )
            if street == self._street and city == self._city:
                return self.get_entries(info)

        raise Exception("Address not found")

    def get_entries(self, info):
        entries = []
        waste_types_info = info.find_all("div", attrs={"class": "pickup-row"})

        for waste_type_info in waste_types_info:
            waste_type = waste_type_info["class"][1].capitalize()
            pickup_date = self.get_date(waste_type_info)
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(date=pickup_date, t=waste_type, icon=icon))

        return entries

    def get_date(self, waste_type_info):
        pickup_date = (
            waste_type_info.find("div", attrs={"class": "pickup-time"})
            .find_all("span")[1]
            .text.split(" ")[1]
        )

        today = date.today()
        pickup_date_day = int(pickup_date.split("/")[0])
        pickup_date_month = int(pickup_date.split("/")[1])
        pickup_date_year = today.year
        if pickup_date_month < today.month:
            pickup_date_year = pickup_date_year + 1

        return date(pickup_date_year, pickup_date_month, int(pickup_date_day))
