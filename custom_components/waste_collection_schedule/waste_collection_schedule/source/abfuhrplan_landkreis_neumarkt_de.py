import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Neumarkt"
DESCRIPTION = "Source for Landkreis Neumarkt."
URL = "https://www.abfuhrplan-landkreis-neumarkt.de"
TEST_CASES = {
    "dietfurt industriestrasse": {"city": "dietfurt", "street": "industriestrasse"},
    "Parsberg, Bogenmühle": {"city": "parsberg", "street": "bogenmuehle"},
}


ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Papiertonne": "mdi:package-variant",
    "Gelber Sack": "mdi:recycle",
}


BASE_API_URL = "https://www.abfuhrplan-landkreis-neumarkt.de"
DATA_ULR = BASE_API_URL + "/{city}/{street}"


def _prepare_arg(arg: str) -> str:
    return (
        arg.lower()
        .strip()
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


class Source:
    def __init__(self, city: str, street: str):
        self._city: str = _prepare_arg(city)
        self._street: str = _prepare_arg(street)
        self._ics = ICS()

    @staticmethod
    def _get_all_elements(url: str) -> list[str]:
        r = requests.get(url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select("li.list-group-item")
        elements = []
        for item in items:
            a = item.select_one("a")
            if not a:
                continue
            href = a.get("href")
            if not isinstance(href, str):
                continue
            href_name = href.split("/")[-1]
            if href_name == _prepare_arg(item.text.lower().strip()):
                elements.append(item.text.strip())
            else:
                elements.append(href_name)
        return elements

    @staticmethod
    def _get_all_cities() -> list[str]:
        return Source._get_all_elements(BASE_API_URL)

    @staticmethod
    def _get_all_streets(city: str) -> list[str]:
        print(f"{BASE_API_URL}/{city}")
        try:
            return Source._get_all_elements(f"{BASE_API_URL}/{city}")
        except requests.exceptions.HTTPError as e:
            print("failed to get streets")
            print(e.response.status_code)
            if e.response.status_code == 404:
                cities = Source._get_all_elements(BASE_API_URL)
                raise SourceArgumentNotFoundWithSuggestions("city", city, cities)
            raise e

    def fetch(self) -> list[Collection]:
        url = DATA_ULR.format(city=self._city, street=self._street)

        # get json file
        r = requests.get(url)
        if r.status_code == 404:
            streets = Source._get_all_streets(self._city)
            raise SourceArgumentNotFoundWithSuggestions("street", self._street, streets)

        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.select_one('form[action="/getical"]')
        if not form:
            raise Exception("Form not found")

        data: dict[str, str | int] = {}
        for input in form.select("input") + form.select("button"):
            name = input.get("name")
            value = input.get("value")
            if not isinstance(name, str):
                continue
            if not isinstance(value, str):
                continue
            data[name] = value

        for selects in form.select("select"):
            name = selects.get("name")
            if not isinstance(name, str):
                continue
            data[name] = 0

        r = requests.post(f"{BASE_API_URL}/getical", data=data)
        r.raise_for_status()

        entries = []
        for date, bin_type in self._ics.convert(r.text):
            icon = ICON_MAP.get(bin_type)  # Collection icon
            entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
