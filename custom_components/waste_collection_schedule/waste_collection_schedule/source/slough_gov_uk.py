import re
from datetime import date

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Slough Borough Council"
DESCRIPTION = "Source for slough.gov.uk services for Slough Borough Council."
URL = "https://www.slough.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "Knolton Way, Montgomery Place": {
        "record_id": 34771,
    },
    "Abbey Close (wheelie bins)": {
        "record_id": 34035,
    },
    "Anslow Place (communal bins)": {
        "record_id": 34069,
    },
    "Search by street name": {
        "street": "Knolton Way, Montgomery Place",
    },
}

ICON_MAP = {
    "Grey bin": "mdi:trash-can",
    "Red bin": "mdi:recycle",
    "Green bin": "mdi:leaf",
    "Food waste": "mdi:food",
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street name",
        "record_id": "Directory record ID",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "The name of your street as listed in the Slough bin directory (e.g. 'Knolton Way, Montgomery Place'). Use this OR record_id, not both.",
        "record_id": "The numeric ID from the Slough bin directory URL (e.g. 34771 from /directory-record/34771/...). Use this OR street, not both.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Search for your street at https://www.slough.gov.uk/bin-collections and note the number from the URL of your matching result (e.g. /directory-record/34771/...). Use that number as record_id, or pass the exact street name as the street argument.",
}

DIRECTORY_SEARCH_URL = "https://www.slough.gov.uk/directory/search"
DIRECTORY_RECORD_BASE_URL = "https://www.slough.gov.uk/directory-record"

BIN_TYPE_MAP = {
    "grey bin": ("Grey bin", ICON_MAP["Grey bin"]),
    "red bin": ("Red bin", ICON_MAP["Red bin"]),
    "green bin": ("Green bin", ICON_MAP["Green bin"]),
    "food waste": ("Food waste", ICON_MAP["Food waste"]),
}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

DATE_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
)


def _parse_date_page(url: str, session: requests.Session) -> list[date]:
    r = session.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    article = soup.find("article")
    if not article:
        return []

    dates = []
    for li in article.find_all("li"):
        text = li.get_text(strip=True)
        m = DATE_RE.search(text)
        if not m:
            continue
        day = int(m.group(1))
        month = MONTHS.get(m.group(2).lower())
        year = int(m.group(3))
        if month is None:
            continue
        try:
            dates.append(date(year, month, day))
        except ValueError:
            continue
    return dates


def _parse_record_page(record_id: int, session: requests.Session) -> list[Collection]:
    # The server validates only the numeric ID; any slug suffix is accepted.
    url = f"{DIRECTORY_RECORD_BASE_URL}/{record_id}/bin-day"
    r = session.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    dl = soup.find("dl")
    if not dl:
        raise SourceArgumentNotFound("record_id", record_id)

    entries = []
    for dt in dl.find_all("dt"):
        heading = dt.get_text(strip=True).lower()
        bin_label = None
        bin_icon = None
        for keyword, (label, icon) in BIN_TYPE_MAP.items():
            if keyword in heading:
                bin_label = label
                bin_icon = icon
                break
        if bin_label is None:
            continue

        dd = dt.find_next_sibling("dd")
        if not dd:
            continue

        link = dd.find("a", href=re.compile(r"/bin-collections/"))
        if link:
            schedule_url = link["href"]
            if not schedule_url.startswith("http"):
                schedule_url = "https://www.slough.gov.uk" + schedule_url
            for d in _parse_date_page(schedule_url, session):
                entries.append(Collection(date=d, t=bin_label, icon=bin_icon))

    if not entries:
        raise SourceArgumentNotFound("record_id", record_id)
    return entries


def _search_records(street: str, session: requests.Session) -> list[dict]:
    r = session.get(
        DIRECTORY_SEARCH_URL,
        params={
            "directoryID": "30",
            "keywords": street,
            "submit": "Search",
        },
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    for a in soup.select("ul.list--record li.list__item a.list__link"):
        href = a.get("href", "")
        m = re.match(r"/directory-record/(\d+)/", href)
        if m:
            results.append(
                {
                    "id": int(m.group(1)),
                    "name": a.get_text(strip=True),
                }
            )
    return results


class Source:
    def __init__(self, record_id: int | None = None, street: str | None = None):
        if record_id is None and street is None:
            raise ValueError("Provide either record_id or street.")
        self._record_id = record_id
        self._street = street

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        if self._record_id is None:
            results = _search_records(self._street, session)
            if not results:
                raise SourceArgumentNotFound("street", self._street)
            if len(results) == 1:
                self._record_id = results[0]["id"]
            else:
                exact = [
                    r for r in results if r["name"].lower() == self._street.lower()
                ]
                if len(exact) == 1:
                    self._record_id = exact[0]["id"]
                else:
                    raise SourceArgumentNotFoundWithSuggestions(
                        "street",
                        self._street,
                        [r["name"] for r in results],
                    )

        return _parse_record_page(self._record_id, session)
