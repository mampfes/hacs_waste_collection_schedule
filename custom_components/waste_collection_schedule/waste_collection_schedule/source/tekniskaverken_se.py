import locale
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Linköping - Tekniska Verken"
DESCRIPTION = "Source for Tekniska Verken in Linköping waste collection"
URL = "https://www.tekniskaverken.se/"
API_URL = (
    "https://www.tekniskaverken.se/privat/avfall-och-atervinning/mat-och-restavfall/"
)
TEST_CASES = {
    "Somewhere": {"street": "Roshagsvägen 2", "city": "Linköping"},
    "Away": {"street": "Roshagsvägen 6", "city": "Linköping"},
    "Home": {"street": "Roshagsvägen 66", "city": "Linköping"},
    "Police": {"street": "Brigadgatan 4", "city": "Linköping"},
}
ICON_MAP = {"Hushållsavfall": "mdi:trash-can", "Trädgårdsavfall": "mdi:leaf"}


class Source:
    def __init__(self, street, city):
        locale.setlocale(locale.LC_ALL, "Swedish_Sweden")
        self._street = street
        self._city = city

    def fetch(self):
        data = {"postback": "true", "street": self._street, "city": self._city}

        response = requests.post(API_URL, params=data)
        response.encoding = "UTF-8"
        soup = BeautifulSoup(response.text, "html.parser")
        addresses = soup.find_all(
            "div", attrs={"class": "wastecollections-selectedaddress"}
        )
        infos = soup.find_all("ul", attrs={"class": "wastecollections-results"})

        for (addressTag, info) in zip(addresses, infos):
            street = addressTag.text.split(",")[0]
            if street == self._street:
                return self.get_entries(info)

        return []

    def get_entries(self, info):
        entries = []
        waste_types_info = info.find_all(
            "li", attrs={"class": "wastecollections-results-item"}
        )

        for waste_type_info in waste_types_info:
            waste_type = waste_type_info.find(
                "strong", attrs={"class": "wastecollections-results-item-type-label"}
            ).text
            pickup_date = self.get_date(waste_type_info)
            icon = ICON_MAP.get(waste_type)
            entries.append(Collection(date=pickup_date, t=waste_type, icon=icon))

        return entries

    def get_date(self, waste_type_info):
        pickup_date_metas = waste_type_info.find_all(
            "div", attrs={"class": "wastecollections-results-item__meta"}
        )

        for pickup_date_meta in pickup_date_metas:
            if "Nästa" in pickup_date_meta.text:
                today = date.today()
                pickup_date_tag = pickup_date_meta.find("strong")
                pickup_datetime = datetime.strptime(pickup_date_tag.text, "%d %B")
                pickup_datetime = pickup_datetime.replace(year=today.year)
                if pickup_datetime.month < today.month:
                    pickup_datetime.replace(year=today.year + 1)

        return pickup_datetime.date()
