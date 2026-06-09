from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons

TITLE = "Hausmannstätten"
DESCRIPTION = "Source for Hausmannstätten."
URL = "https://www.hausmannstaetten.gv.at"
TEST_CASES: dict[str, dict] = {"Testcase": {}}
COUNTRY = "at"


ICON_MAP = {
    "restmüll i": Icons.GENERAL_WASTE,
    "restmüll ii": Icons.GENERAL_WASTE,
    "restmüll ii + 1100": Icons.GENERAL_WASTE,
    "bioabfall": Icons.BIO_KITCHEN,
    "altpapier i": Icons.PAPER,
    "altpapier ii": Icons.PAPER,
    "sperrmüll asz-fernitz": Icons.BULKY,
    "leicht- und metallverpackungen": Icons.METAL,
}

API_URL = "https://hausmannstaetten.gv.at/terminkalender"


class Source:
    def __init__(self):
        pass

    def _get_trash(self, table):
        trash_collection = []
        content = list(table.contents)[1]
        articles = content.findAll("div", "article")
        for article in articles:
            title = self._get_trash_type(article)
            date = self._get_date(article)
            icon = ICON_MAP.get(title.lower())
            time = self._get_time(article)
            if time:
                title = f"{title} ({time})"
            trash_collection.append(Collection(date=date, t=title, icon=icon))
        return trash_collection

    def _get_trash_type(self, article):
        return article.find("a").get("title", None)

    def _get_date(self, article):
        date_string = article.find("span", class_="date")
        return datetime.strptime(date_string.text.strip(), "%d.%m.%Y").date()

    def _get_time(self, article):
        time = article.find("span", class_="time")
        if not time:
            return None
        return time.text.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find(id="content-tab-umweltkalender")

        trash_type = self._get_trash(table)
        return trash_type
