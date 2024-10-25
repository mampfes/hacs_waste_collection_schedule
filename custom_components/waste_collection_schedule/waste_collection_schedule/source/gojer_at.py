from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "GOJER"
DESCRIPTION = "Source for GOJER."
URL = "https://www.gojer.at/"
TEST_CASES = {
    "Ruden Kleindiex": {"municipality": "Ruden", "city": "Kleindiex"},
    "Frantschach-St. Gertraud": {
        "municipality": "Frantschach-St. Gertraud",
        "city": "Trum-und Prössinggraben",
    },
    "St. Kanzian am Klopeiner See, Vesielach": {
        "municipality": "St. Kanzian am Klopeiner See",
        "city": "Vesielach",
    },
}


ICON_MAP = {
    "Bioabfall": "mdi:leaf",
    "Hausmüll": "mdi:trash-can",
    "Plastikflaschen": "mdi:bottle-soda-classic",
    "Altpapier": "mdi:package-variant",
    "Metallverpackungen": "mdi:anvil",
    "Altstoffsammelzentrum": "mdi:factory",
}


API_URL = "https://www.gojer.at/service/abfuhrkalender.html"
CITY_URL = "https://www.gojer.at/ortausgemeinde.html"


PARAM_TRANSLATIONS = {
    "de": {
        "municipality": "Gemeinde",
        "city": "Ort",
    }
}


def cmp(a: str, b: str) -> bool:
    for char in (" ", ",", ".", "_", "-"):
        a = a.replace(char, "")
        b = b.replace(char, "")

    return a.lower() == b.lower()


class Source:
    def __init__(self, municipality: str, city: str):
        self._municipality: str = municipality
        self._city: str = city

        self._bin_types: dict[str, str] | None = None

    @staticmethod
    def get_municipalities(soup: BeautifulSoup | None = None) -> dict[str, str]:
        if soup is None:
            r = requests.get(API_URL)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        municipalities = dict[str, str]()
        select = soup.select_one("select#gemeindewahl")

        if not select:
            raise Exception("Could not find municipality select")

        for option in select.select("option"):
            if option["value"] in ("", "base"):
                continue
            municipalities[option["value"]] = option.text.strip()
        return municipalities

    @staticmethod
    def get_bin_type_dict(soup: BeautifulSoup | None = None) -> dict[str, str]:
        if soup is None:
            r = requests.get(API_URL)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        bin_types = dict[str, str]()

        for checkbox in soup.select('input[type="checkbox"]'):
            attrs = checkbox.attrs
            if "name" not in attrs or "value" not in attrs:
                continue
            bin_types[attrs["name"]] = attrs["value"]
        return bin_types

    @staticmethod
    def get_city(mun: str) -> list[str]:
        r = requests.get(CITY_URL, params={"choice": mun})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cities = []
        for option in soup.select("option"):
            cities.append(option.text.strip())
        return cities

    def match_municipality(self, muns: dict[str, str]) -> str:
        for val, text in muns.items():
            if cmp(val, self._municipality) or cmp(text, self._municipality):
                return val
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", self._municipality, list(muns.values())
        )

    def match_city(self, cities: list[str]):
        for city in cities:
            if cmp(city, self._city):
                return city
        raise SourceArgumentNotFoundWithSuggestions("city", self._city, cities)

    def fetch(self) -> list[Collection]:
        soup: BeautifulSoup | None = None
        if not self._bin_types:
            r = requests.get(API_URL)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            self._bin_types = self.get_bin_type_dict(soup)
            self._municipality = self.match_municipality(self.get_municipalities(soup))
            self._city = self.match_city(self.get_city(self._municipality))

        if not self._bin_types:
            raise Exception("Bin types not loaded, this should not happen")

        params = {
            "gemeindewahl": self._municipality,
            "ortswahl": self._city,
            **self._bin_types,
        }
        r = requests.get(API_URL, params=params)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        if soup.select_one("select#gemeindewahl"):
            # Request failed and returned default page
            self.match_municipality(
                self.get_municipalities(soup)
            )  # should raise exception if municipality is not found
            self.match_city(
                self.get_city(self._municipality)
            )  # should raise exception if city is not found
            raise Exception("Unknown error occurred")

        entries = []
        last_date_str = ""
        for tr in soup.select("tr.mitBorder, tr.ohneBorder"):
            tds = tr.select("td")
            if len(tds) < 2:
                continue
            if tds[0].text.strip() == "":
                date_str = last_date_str
            else:
                date_str = tds[0].text.strip().split(" ")[1]
                last_date_str = date_str
            date = datetime.strptime(date_str, "%d.%m.%y").date()
            bin_tag = tds[1]
            span = bin_tag.select_one("span")
            if span:
                span.decompose()
            bin_type = bin_tag.text.strip()
            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
