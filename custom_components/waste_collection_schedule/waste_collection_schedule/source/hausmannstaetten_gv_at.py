from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Hausmannstätten"
DESCRIPTION = "Source for Hausmannstätten."
URL = "https://www.hausmannstaetten.gv.at"
TEST_CASES = {
    "Testcase": {}
}
COUNTRY = "at"


ICON_MAP = {
    "restmüll i": "mdi:trash-can",
    "restmüll ii": "mdi:trash-can",
    "restmüll ii + 1100": "mdi:trash-can",
    "bioabfall": "mdi:leaf",
    "altpapier i": "mdi:package-variant",
    "altpapier ii": "mdi:package-variant",
    "sperrmüll asz-fernitz": "mdi:factory",
    "leicht- und metallverpackungen": "mdi:recycle",
}

API_URL = "https://hausmannstaetten.gv.at/terminkalender"

class Source:
    def __init__(self):
        pass

    def _get_trash(self, table):
        trash_collection = []
        content = list(table.contents)[1]
        articles = content.findAll('div', 'article')
        for article in articles:
            title = self._get_trash_type(article)
            date = self._get_date(article)
            icon=ICON_MAP.get(title.lower())
            time = self._get_time(article)
            if time:
                title = "{} ({})".format(title, time)
            trash_collection.append(Collection(date=date, t=title, icon=icon))
        return trash_collection

    def _get_trash_type(self, article):
        return article.find('a').get('title', None)

    def _get_date(self, article):
        date_string = article.find('span', class_='date')
        return datetime.strptime(date_string.text.strip(), '%d.%m.%Y').date()

    def _get_time(self, article):
        time = article.find('span', class_='time')
        if not time:
            return None
        return time.text.strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find(id='content-tab-umweltkalender')

        trash_type = self._get_trash(table)
        return trash_type
