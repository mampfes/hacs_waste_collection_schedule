import logging
import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

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
_LOGGER = logging.getLogger(__name__)
ICON_MAP = {
    "Recycling (blue-lidded bin)": Icons.RECYCLING,
    "Household waste (green-lidded bin)": Icons.GENERAL_WASTE,
    "Garden waste (brown-lidded bin)": Icons.GARDEN,
    "Food waste caddy": Icons.BIO_KITCHEN,
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


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


class Source:
    def __init__(self, street: str):
        self._street: str = street

    def append_year(self, d: str) -> date:
        # Website dates don't have the year.
        # Append the current year, and then check to see if the date is in the past.
        # If it is, increment the year by 1.
        d = _normalize_space(d)

        today: date = datetime.now().date()
        this_year: int = today.year
        dt: date = datetime.strptime(f"{d} {this_year}", "%A %d %B %Y").date()
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
        r = s.get(API_URLS["search"], headers=HEADERS, params=params, timeout=30)
        soup: BeautifulSoup = BeautifulSoup(r.content, "html.parser")
        list_links: list = soup.find_all("a", {"class": "list__link"})
        directory_record: str | None = None
        for link in list_links:
            if self._street.upper() in link.text.upper():
                directory_record = link["href"]
                break

        if directory_record is None:
            raise RuntimeError(f"Street '{self._street}' not found")

        # use directory record to get collection day
        r = s.get(
            API_URLS["directory_record"] + directory_record, headers=HEADERS, timeout=30
        )
        soup = BeautifulSoup(r.content, "html.parser")
        buttons: list = soup.find_all("a", {"class": "button"})
        schedule: str | None = None
        for button in buttons:
            if "bin" in button["href"]:
                schedule = button["href"]
                break

        if schedule is None:
            raise RuntimeError(
                f"No bin collection calendar link found for '{self._street}'"
            )

        # fetch collection schedule page
        r = s.get(schedule, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.content, "html.parser")
        entries: list[Collection] = []

        # Schedule page contains one `<table>` per month.
        # Columns: "Day and date", waste-type headers...
        # Rows: date cell, then "Yes"/"No" per waste type.
        for table in soup.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue
            headers = [
                th.get_text(separator="\n").split("\n")[0].strip()
                for th in thead.find_all("th")
            ]
            if not headers or headers[0] != "Day and date":
                continue
            waste_types = headers[1:]

            tbody = table.find("tbody")
            if not tbody:
                continue
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                date_text = _normalize_space(cells[0].get_text())
                try:
                    waste_date = self.append_year(date_text)
                except Exception as e:
                    _LOGGER.warning(f"Error parsing date '{date_text}': {e}")
                    continue
                for i, waste_type in enumerate(waste_types):
                    if i + 1 >= len(cells):
                        break
                    if _normalize_space(cells[i + 1].get_text()).lower() == "yes":
                        entries.append(
                            Collection(
                                date=waste_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type, Icons.GENERAL_WASTE),
                            )
                        )

        return entries
