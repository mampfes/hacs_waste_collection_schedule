from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Coventry City Council"
DESCRIPTION = "Source for waste collection services for Coventry City Council"
URL = "https://www.coventry.gov.uk/"

HEADERS = {"user-agent": "Mozilla/5.0"}
API_URLS = {
    "search": "https://www.coventry.gov.uk/directory/search",
    "directory_record": "https://www.coventry.gov.uk",
}
TEST_CASES = {
    "Test_001": {
        "street": "Linwood Drive",
    },
    "Test_002": {
        "street": "Cromwell Lane",
    },
    "Test_003": {
        "street": "Lutterworth Road",
    },
}
ICON_MAP = {
    "green-lidded (rubbish) bin": "mdi:trash-can",
    "blue-lidded (recycling) bin": "mdi:recycle",
    "brown-lidded (garden waste) bin": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Your street name, as it appears on the Coventry City Council website",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Your street name, as it appears on the Coventry City Council website",
    }
}


class Source:
    def __init__(self, street: str):
        self._street: str = street

    def append_year(self, d: str) -> date:
        # Website dates don't have the year.
        # Append the current year, and then check to see if the date is in the past.
        # If it is, increment the year by 1.
        today: date = datetime.now().date()
        year: int = today.year
        dt: date = datetime.strptime(f"{d} {str(year)}", "%A %d %B %Y").date()
        if (dt - today) < timedelta(days=-31):
            dt = dt.replace(year=dt.year + 1)
        return dt

    def fetch(self) -> list[Collection]:
        s = requests.Session()

        # search for address to get directory record
        params: dict = {
            "directoryID": "82",
            "showInMap": "",
            "keywords": self._street,
            "search": "Search",
        }
        r = s.get(API_URLS["search"], headers=HEADERS, params=params)
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        list_links: list = soup.find_all("a", {"class": "list__link"})
        for link in list_links:
            if self._street.upper() in link.text.upper():
                directory_record: str = link["href"]

        # use directory record to get collection day
        r = s.get(API_URLS["directory_record"] + directory_record, headers=HEADERS)
        soup = BeautifulSoup(r.content, "html.parser")
        buttons: list = soup.find_all("a", {"class": "button"})
        for button in buttons:
            if "bins" in button["href"]:
                schedule: str = button["href"]

        # use collction day to get schedule
        r = s.get(schedule, headers=HEADERS)
        soup = BeautifulSoup(r.content, "html.parser")
        widgets: list = soup.find_all("div", {"class": "widget-content"})
        entries: list = []
        for widget in widgets:
            list_items: list = widget.find_all("li")
            for item in list_items:
                waste_date: date = self.append_year(item.text.split(": ")[0])
                waste_types: list = item.text.split(": ")[1].split(" and ")
                for waste_type in waste_types:
                    entries.append(
                        Collection(
                            date=waste_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
