from datetime import date, timedelta
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Westminster City Council"
DESCRIPTION = "Source for Westminster City Council (London, UK) bin collections."
URL = "https://www.westminster.gov.uk"
COUNTRY = "uk"

API_URL = (
    "https://transact.westminster.gov.uk/env/streetreport.aspx?Street=NA&USRN={usrn}"
)

TEST_CASES = {
    "Shirland Mews (short street)": {"usrn": "8400172"},
    "Shirland Road (long street)": {"usrn": 8400243},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}

SOURCE_CODEOWNERS = ["@parmymansam"]

# The recurring weekly schedule has no end date; project this far ahead.
_HORIZON_DAYS = 365

# Waste type for the rubbish panel (that table has no per-row type column).
RUBBISH_TYPE = "Residential rubbish and commercial waste"

ICON_MAP = {
    "Residential rubbish and commercial waste": Icons.GENERAL_WASTE,
    "Food Recycling Collection": Icons.BIO_KITCHEN,
    "Recycling Collection": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "You need the USRN (Unique Street Reference Number) for your street. Find it "
        "by searching your street on https://www.findmyaddress.co.uk or by inspecting "
        "the USRN value in the URL of Westminster's own street-report search at "
        "https://transact.westminster.gov.uk/env/streetreport.aspx"
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "usrn": "USRN",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "usrn": "Unique Street Reference Number (USRN) for your street.",
    },
}

_WEEKDAYS = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _parse_days(text: str) -> set[int]:
    """Expand a day cell (e.g. 'Tue, Fri', 'Mon-Fri') into weekday() indices."""
    text = text.replace("\xa0", " ")
    result: set[int] = set()
    for token in text.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if "-" in token:
            start, _, end = token.partition("-")
            s = _WEEKDAYS.get(start.strip()[:3])
            e = _WEEKDAYS.get(end.strip()[:3])
            if s is None or e is None:
                continue
            if s <= e:
                result.update(range(s, e + 1))
            else:  # wrap-around range, e.g. Sat-Mon
                result.update(range(s, 7))
                result.update(range(0, e + 1))
        else:
            v = _WEEKDAYS.get(token[:3])
            if v is not None:
                result.add(v)
    return result


def _get_icon(waste_type: str) -> Icons | None:
    """Return the mapped Icons member for a waste type, or None if unmapped."""
    return ICON_MAP.get(waste_type)


def _column_index(table) -> dict[str, int]:
    """Map lowercased header-cell text -> column index for a table's first row."""
    header = table.find("tr")
    cols: dict[str, int] = {}
    if header is None:
        return cols
    for i, cell in enumerate(header.find_all(["th", "td"])):
        cols[cell.get_text(strip=True).lower()] = i
    return cols


def _data_rows(table):
    """All rows after the header row."""
    return table.find_all("tr")[1:]


def _days_from_row(cells, cols) -> set[int]:
    """Union of Week Days + Weekend Days cells for one row."""
    days: set[int] = set()
    for key in ("week days", "weekend days"):
        idx = cols.get(key)
        if idx is not None and idx < len(cells):
            days |= _parse_days(cells[idx].get_text())
    return days


def _extract_pairs(soup) -> set[tuple[str, int]]:
    """Parse the rubbish + recycling panels into deduped (waste_type, weekday) pairs."""
    pairs: set[tuple[str, int]] = set()

    rubbish = soup.find("div", id="pnlrubbishcollection")
    if rubbish is not None:
        table = rubbish.find("table")
        if table is not None:
            cols = _column_index(table)
            for row in _data_rows(table):
                cells = row.find_all(["td", "th"])
                # A row with a different cell count than the header (e.g. a
                # merged/omitted cell) can't be trusted to align positionally
                # with `cols` — skip it rather than silently reading the
                # wrong column.
                if len(cells) != len(cols):
                    continue
                for weekday in _days_from_row(cells, cols):
                    pairs.add((RUBBISH_TYPE, weekday))

    recycling = soup.find("div", id="pnlrecyclingcollections")
    if recycling is not None:
        table = recycling.find("table")
        if table is not None:
            cols = _column_index(table)
            sd = cols.get("service description")
            for row in _data_rows(table):
                cells = row.find_all(["td", "th"])
                if len(cells) != len(cols):
                    continue
                if sd is None or sd >= len(cells):
                    continue
                waste_type = cells[sd].get_text(strip=True)
                if not waste_type:
                    continue
                for weekday in _days_from_row(cells, cols):
                    pairs.add((waste_type, weekday))

    return pairs


class Source:
    def __init__(self, usrn):
        self._usrn = str(usrn)

    def fetch(self) -> list[Collection]:
        response = requests.get(
            API_URL.format(usrn=quote(self._usrn)), headers=HEADERS, timeout=30
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        pairs = _extract_pairs(soup)
        if not pairs:
            raise SourceArgumentNotFound(
                "usrn",
                f"No collections found for USRN '{self._usrn}'. Check the USRN is correct.",
            )

        today = date.today()
        horizon_end = today + timedelta(days=_HORIZON_DAYS)

        entries: list[Collection] = []
        for waste_type, weekday in sorted(pairs):
            offset = (weekday - today.weekday()) % 7
            collection_date = today + timedelta(days=offset)
            icon = _get_icon(waste_type)
            while collection_date <= horizon_end:
                entries.append(
                    Collection(date=collection_date, t=waste_type, icon=icon)
                )
                collection_date += timedelta(days=7)

        return entries
