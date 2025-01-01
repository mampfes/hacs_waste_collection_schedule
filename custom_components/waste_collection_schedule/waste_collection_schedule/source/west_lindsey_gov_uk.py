import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "West Lindsey District Council"
DESCRIPTION = "Source for West Lindsey District Council, Lincolnshire, UK."
URL = "https://www.west-lindsey.gov.uk"
HEADERS = {
    "user-agent": "Mozilla/5.0",
    "referer": "https://www.west-lindsey.gov.uk/",
    "host": "wlnk.statmap.co.uk",
}
TEST_CASES = {
    "Test_001": {"x": 509762, "y": 384493, "id": 919},
    # "Test_002": {"uprn": "100090989776"},
    # "Test_003": {"uprn": "10000021270"},
    # "Test_004": {"uprn": 100090969937},
}
ICON_MAP = {
    "BLACK": "mdi:trash-can",
    "BLUE": "mdi:recycle",
    "PURPLE": "mdi:newspaper",
    "GREEN": "mdi:leaf",
}
REGEX = r"(BLACK|BLUE|PURPLE|GREEN).+,\s(\d+\/\d+).+\s(\d+\/\d+)"


class Source:
    def __init__(self, x: int | str, y: int | str, id: int | str):
        self._query: str = f"x={str(x)};y={str(y)};id={str(id)}"

    def append_year(self, d: list) -> list[date]:
        today = datetime.now().date()
        year: int = today.year
        dates: list[date] = []
        for dt in d:
            dt = datetime.strptime(f"{dt}/{str(year)}", "%d/%m/%Y").date()
            if (dt - today) < timedelta(days=-31):
                dt = dt.replace(year=dt.year + 1)
            dates.append(dt)
        return dates

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        params = {
            "script": r"\Cluster\Cluster.AuroraScript$",
            "taskId": "bins",
            "format": "js",
            "updateOnly": "true",
            "query": self._query,
        }
        r = s.get(
            "https://wlnk.statmap.co.uk/map/Cluster.svc/getpage",
            headers=HEADERS,
            params=params,
        )
        r.raise_for_status

        soup: BeautifulSoup = BeautifulSoup(
            r.content.decode("unicode-escape"), "html.parser"
        )

        list_item = soup.find("li", {"class": "auroraListItem"})
        lis = list_item.find_all("li")

        entries: list = []
        for li in lis:
            details = re.findall(REGEX, li.text.split(".")[0])
            flattened: list = [item for sublist in details for item in sublist]
            waste_type: str = flattened[0]
            waste_dates = self.append_year(flattened[1:])
            for dt in waste_dates:
                entries.append(
                    Collection(date=dt, t=waste_type, icon=ICON_MAP.get(waste_type))
                )

        return entries
