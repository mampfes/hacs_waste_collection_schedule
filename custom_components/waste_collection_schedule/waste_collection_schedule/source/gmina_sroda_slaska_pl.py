import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Gmina Środa Śląska"
DESCRIPTION = "Source for Gmina Środa Śląska, Poland"
URL = "https://srodowisko.srodaslaska.pl/gospodarka-odpadami/harmonogram-odbioru-odpadow-komunalnych/"
SCHEDULE_URL = "https://www.com-d.pl/komunalne/harm/sroda-slaska"
COUNTRY = "pl"
TEST_CASES = {
    "Szczepanów": {"location": "szczepanow"},
}

ICON_MAP = {
    "1xmc-odpady-szklo": Icons.GLASS,
    "inne-odpady-rozne": Icons.TEXTILE,
    "inne-odpady-zbiorki": Icons.BULKY,
    "inne-odpady-papier": Icons.PAPER,
    "t-odpady-biodegradowalne": Icons.ORGANIC,
    "t-odpady-zmieszane": Icons.GENERAL_WASTE,
    "tp-odpady-metaletworzywa": Icons.RECYCLING,
}

TYPE_MAP = {
    "1xmc-odpady-szklo": "Szkło",
    "inne-odpady-rozne": "Tekstylia i odzież",
    "inne-odpady-zbiorki": "Odpady wielkogabarytowe",
    "inne-odpady-papier": "Papier",
    "t-odpady-biodegradowalne": "Odpady biodegradowalne",
    "t-odpady-zmieszane": "Zmieszane odpady komunalne",
    "tp-odpady-metaletworzywa": "Metale i tworzywa sztuczne",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Visit https://www.com-d.pl/komunalne/harm/sroda-slaska, select your locality or Środa Śląska district, and enter the final part of its URL.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "location": "Locality or district URL slug from the COM-D schedule page",
    },
}


class Source:
    def __init__(self, location):
        self._location = location

    def fetch(self):
        entries = []
        seen = set()
        response = requests.get(f"{SCHEDULE_URL}/{self._location}", timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        schedule_table = next(
            table
            for table in soup.find_all("table")
            if table.find("th", string="Frakcja")
        )
        category_urls = {
            link["href"] for link in schedule_table.select('a[href*="/sroda-slaska/"]')
        }

        for category_url in category_urls:
            category = category_url.rsplit("/", 1)[-1]
            category_response = requests.get(
                f"https://www.com-d.pl{category_url}", timeout=30
            )
            category_response.raise_for_status()
            category_soup = BeautifulSoup(category_response.text, "html.parser")

            for collection_day in category_soup.select("td.highlighted[data-date]"):
                collection_date = datetime.datetime.strptime(
                    collection_day["data-date"], "%Y-%m-%d"
                ).date()
                entry = (collection_date, category)
                if entry in seen:
                    continue
                seen.add(entry)
                entries.append(
                    Collection(
                        date=collection_date,
                        t=TYPE_MAP.get(category, category.capitalize()),
                        icon=ICON_MAP.get(category),
                    )
                )

        return entries
