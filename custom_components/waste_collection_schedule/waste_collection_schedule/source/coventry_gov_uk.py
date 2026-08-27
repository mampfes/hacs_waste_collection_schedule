import logging
import re
from datetime import date, datetime

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

        # Use the collection calendar link to get the current schedule.
        r = s.get(schedule, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        entries: list[Collection] = []

        # Coventry changed its calendars from colon-delimited prose to one
        # table per month. Each waste column contains Yes/No for every date.
        today = date.today()
        for table in soup.select("div.editor table"):
            heading = table.find_previous(["h2", "h3"])
            year_match = re.search(
                r"\b(20\d{2})\b", heading.get_text() if heading else ""
            )
            if year_match is None:
                continue
            year = year_match.group(1)

            headers = [
                _normalize_space(cell.get_text(" ", strip=True))
                for cell in table.select("thead th")
            ]
            if len(headers) < 2:
                continue

            for row in table.select("tbody tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) != len(headers):
                    continue
                date_text = _normalize_space(cells[0].get_text(" ", strip=True))
                try:
                    waste_date = datetime.strptime(
                        f"{date_text} {year}", "%A %d %B %Y"
                    ).date()
                except ValueError:
                    _LOGGER.warning(
                        "Could not parse Coventry collection date '%s'", date_text
                    )
                    continue
                if waste_date < today:
                    continue

                for waste_type, cell in zip(headers[1:], cells[1:], strict=True):
                    if not re.search(r"\byes\b", cell.get_text(" ", strip=True), re.I):
                        continue
                    entries.append(
                        Collection(
                            date=waste_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
