import logging
import re
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
_LOGGER = logging.getLogger(__name__)
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

        # use collction day to get schedule
        r = s.get(schedule, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.content, "html.parser")
        entries: list[Collection] = []

        # Schedule page contains month widgets with <div class="editor"> text and <br> separators.
        for editor in soup.select("div.widget--content div.widget-content div.editor"):
            current_date_part: str | None = None
            current_types_parts: list[str] = []

            def flush() -> None:
                if current_date_part is None:
                    return

                try:
                    waste_date = self.append_year(current_date_part)
                    types_part = _normalize_space(" ".join(current_types_parts))
                    for waste_type in (
                        t.strip()
                        for t in re.split(r"\s+and\s+", types_part)
                        if t.strip()
                    ):
                        entries.append(
                            Collection(
                                date=waste_date,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type, "mdi:trash-can"),
                            )
                        )
                except Exception as e:
                    _LOGGER.warning(f"Error processing item '{current_date_part}': {e}")

            for raw_line in editor.get_text("\n", strip=True).splitlines():
                line = _normalize_space(raw_line)
                if not line:
                    continue

                if ":" in line:
                    flush()
                    date_part, types_part = (p.strip() for p in line.split(":", 1))
                    current_date_part = date_part
                    current_types_parts = [types_part] if types_part else []
                elif current_date_part is not None:
                    current_types_parts.append(line)

            flush()

        return entries
