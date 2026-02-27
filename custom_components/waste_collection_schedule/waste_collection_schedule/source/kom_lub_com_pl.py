from __future__ import annotations

import datetime as dt
import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "KOM-LUB (Luboń, PL)"
DESCRIPTION = "Scrapes waste collection schedule by district (1..7) from kom-lub.com.pl."
URL = "https://kom-lub.com.pl/aktualny-harmonogram-wywozow/"

_LOGGER = logging.getLogger(__name__)

######################################################################
# TEST CASES
######################################################################
TEST_CASES = {
    "TestDistrict1": {"district": 1},
    "TestDistrict2": {"district": 2},
    "TestDistrict3": {"district": 3},
    "TestDistrict4": {"district": 4},
    "TestDistrict5": {"district": 5},
    "TestDistrict6": {"district": 6},
    "TestDistrict7": {"district": 7},
}

# Provide (don’t comment out) so the GUI has instructions.
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "pl": """
1) Wejdź na stronę z rejonami (ulice -> rejon):
   kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/

2) W tabelach znajdziesz nagłówki rejonów: R I, R II, ..., R VII.

3) Wybierz numer district zgodnie z mapowaniem:
   - R I   -> 1
   - R II  -> 2
   - R III -> 3
   - R IV  -> 4
   - R V   -> 5
   - R VI  -> 6
   - R VII -> 7
""".strip()
}

INPUT_ARGUMENTS = [
    {
        "name": "district",
        "type": "select",
        "description": "Wybierz rejon (R I .. R VII).",
        "default": 1,
        "options": [
            {"value": 1, "label": "R I (1)"},
            {"value": 2, "label": "R II (2)"},
            {"value": 3, "label": "R III (3)"},
            {"value": 4, "label": "R IV (4)"},
            {"value": 5, "label": "R V (5)"},
            {"value": 6, "label": "R VI (6)"},
            {"value": 7, "label": "R VII (7)"},
        ],
    }
]

######################################################################
# Types / constants
######################################################################
DayList = list[int]
Cols = list[DayList]  # exactly 6 columns in order: mixed, glass, plastics, paper, bulky, bio
MonthRow = tuple[int, Cols]  # (month_number, cols)
DistrictRows = list[MonthRow]
QuarterKey = tuple[str, int]  # (year_str, quarter_number)
QuarterData = dict[str, DistrictRows]  # district -> rows
AllData = dict[QuarterKey, QuarterData]

COL_NAMES = ["Mixed", "Glass", "Plastics", "Paper", "Bulky", "Bio"]

ICON_BY_TYPE: dict[str, str] = {
    "Mixed": "mdi:trash-can",
    "Glass": "mdi:glass-wine",
    "Plastics": "mdi:recycle",
    "Paper": "mdi:newspaper-variant-multiple",
    "Bulky": "mdi:sofa",
    "Bio": "mdi:leaf",
}

_DISTRICT_ROMAN: dict[int, str] = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}
_REGION_RE = re.compile(r"^R\s*[IVX]+$", re.IGNORECASE)

_QUARTER_IN_TEXT_RE = re.compile(r"\b(I|II|III|IV)\s+kwartał\s+(20\d{2})\b", re.IGNORECASE)

_ROMAN_MONTH = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
}


@dataclass(frozen=True)
class ParsedRow:
    month: int
    mixed: DayList
    glass: DayList
    plastics: DayList
    paper: DayList
    bulky: DayList
    bio: DayList


def safe_date(y: int, m: int, d: int) -> Optional[dt.date]:
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def extract_day_numbers(text: str) -> DayList:
    """Pull any 1-2 digit numbers from the cell."""
    return [int(x) for x in re.findall(r"\d{1,2}", text or "")]


######################################################################
# Argument handling
######################################################################
def normalize_district(district: int | str | None) -> str:
    """Accepts 1..7 (int/str) and returns 'R I' .. 'R VII'."""
    if district is None or str(district).strip() == "":
        raise SourceArgumentRequired("district", "Podaj numer rejonu 1–7 (R I .. R VII).")

    try:
        n = int(district)
    except Exception:
        raise SourceArgumentException(
            "district",
            f"Nieprawidłowa wartość district={district!r}. Podaj liczbę 1–7.",
        )

    if n not in _DISTRICT_ROMAN:
        raise SourceArgumentException(
            "district",
            f"Nieprawidłowy district={n}. Dozwolone wartości: 1–7.",
        )

    return f"R {_DISTRICT_ROMAN[n]}"


######################################################################
# HTML fetching / parsing
######################################################################
def fetch_soup() -> BeautifulSoup:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    _LOGGER.debug("Fetched %s bytes from %s", len(r.text), URL)
    return BeautifulSoup(r.content, "html.parser")


def extract_tables(soup: BeautifulSoup) -> dict[str, Tag]:
    """
    Finds all quarter tables and returns: {title: table_tag}.
    Title is like: "I kwartał 2026".

    Current KOM-LUB HTML pattern:
    - quarter label is in a div containing "Harmonogram wywozów" + e.g. "I kwartał 2026"
    - the following table contains all districts (R I..R VII)
    """
    result: dict[str, Tag] = {}

    entry_content = soup.select_one("div.entry-content")
    if not entry_content:
        raise Exception("Nie znaleziono div.entry-content (zmienił się układ strony?).")

    for div in entry_content.find_all("div"):
        txt = div.get_text(" ", strip=True)
        if "Harmonogram wywozów" not in txt:
            continue

        m = _QUARTER_IN_TEXT_RE.search(txt)
        if not m:
            continue

        q_roman = m.group(1).upper()
        year = m.group(2)
        title = f"{q_roman} kwartał {year}"

        table = div.find_next("table")
        if not table:
            continue

        result[title] = table

    _LOGGER.debug("Found %d quarter tables: %s", len(result), list(result.keys()))
    return result


def parse_quarter_key(title: str) -> QuarterKey:
    """Find quarter roman + 4-digit year anywhere in the title."""
    q_map = {"I": 1, "II": 2, "III": 3, "IV": 4}

    m_q = re.search(r"\b(I|II|III|IV)\b", title)
    m_y = re.search(r"\b(20\d{2})\b", title)
    if not m_q or not m_y:
        raise ValueError(f"Cannot parse quarter/year from title: {title!r}")

    return (m_y.group(1), q_map[m_q.group(1)])


def extract_month_row(tr: Tag) -> MonthRow:
    """
    Returns (month, cols) where cols are 6 columns [mixed, glass, plastics, paper, bulky, bio].

    We expand td colspans, because rows with empty middle columns can be represented
    by fewer cells in HTML.
    """
    th = tr.find("th")
    if not th:
        raise ValueError("Unexpected row without <th> month header")

    month_token = th.get_text(strip=True).upper()
    month = _ROMAN_MONTH.get(month_token)
    if not month:
        raise ValueError(f"Unexpected month token: {month_token!r}")

    tds = tr.find_all("td")
    cols: Cols = []

    for td in tds:
        text = td.get_text(" ", strip=True)
        days = extract_day_numbers(text)
        colspan = int(td.get("colspan", 1) or 1)
        value = days if text else []

        for _ in range(colspan):
            cols.append(value)

    # Normalize to exactly 6 columns
    if len(cols) != 6:
        _LOGGER.debug(
            "Month %s: after colspan expansion cols=%d (expected 6). cols=%s",
            month_token,
            len(cols),
            cols,
        )

    while len(cols) < 6:
        cols.append([])
    cols = cols[:6]

    return (month, cols)


def split_table_by_district(table: Tag) -> QuarterData:
    district_rows: QuarterData = {}
    cur_district: str | None = None

    thead = table.find("thead")
    if thead:
        header_tr = thead.find("tr")
        if header_tr:
            first_th = header_tr.find("th")
            if first_th:
                th_text = first_th.get_text(" ", strip=True).upper().strip()
                if _REGION_RE.match(th_text):
                    cur_district = th_text
                    district_rows.setdefault(cur_district, [])

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("No tbody found")

    for tr in tbody.find_all("tr", recursive=False):
        first_th = tr.find("th")
        if not first_th:
            continue

        th_text = first_th.get_text(" ", strip=True).upper().strip()

        # district header row
        if _REGION_RE.match(th_text):
            cur_district = th_text
            district_rows.setdefault(cur_district, [])
            continue

        # month row must have tds
        if not tr.find_all("td"):
            continue

        if cur_district is None:
            cur_district = "R I"
            district_rows.setdefault(cur_district, [])
            _LOGGER.debug("No district header found before month rows; defaulting to R I")

        district_rows[cur_district].append(extract_month_row(tr))

    return district_rows


def parse_tables_dict(tables_by_title: dict[str, Tag]) -> AllData:
    """(year_str, quarter) -> (district -> list[(month, cols)])"""
    out: AllData = {}

    for title, table in tables_by_title.items():
        key = parse_quarter_key(title)
        out[key] = split_table_by_district(table)
        _LOGGER.debug("Parsed table %r -> key=%s districts=%s", title, key, list(out[key].keys()))

    return out


######################################################################
# Conversion to Collections
######################################################################
def parsed_row_from_cols(month: int, cols: Cols) -> ParsedRow:
    return ParsedRow(
        month=month,
        mixed=cols[0],
        glass=cols[1],
        plastics=cols[2],
        paper=cols[3],
        bulky=cols[4],
        bio=cols[5],
    )


def collections_from_row(year: int, row: ParsedRow) -> list[Collection]:
    entries: list[Collection] = []

    def add(days: DayList, name: str) -> None:
        icon = ICON_BY_TYPE.get(name)
        for d in days:
            dt_ = safe_date(year, row.month, d)
            if dt_:
                entries.append(Collection(date=dt_, t=name, icon=icon))

    add(row.mixed, "Mixed")
    add(row.glass, "Glass")
    add(row.plastics, "Plastics")
    add(row.paper, "Paper")
    add(row.bulky, "Bulky")
    add(row.bio, "Bio")

    return entries


def scrape_for_region(soup: BeautifulSoup, region: str, district_value: int | str) -> list[Collection]:
    tables = extract_tables(soup)
    if not tables:
        raise Exception("Nie znaleziono tabel harmonogramu na stronie (zmienił się układ strony?).")

    sections = parse_tables_dict(tables)
    if not sections:
        raise Exception("Nie udało się sparsować tabel harmonogramu (brak danych po parsowaniu).")

    entries: list[Collection] = []
    found_region_anywhere = False

    for (year_str, _quarter), regions in sections.items():
        district_rows = regions.get(region)
        if not district_rows:
            continue

        found_region_anywhere = True
        year = int(year_str)

        for month, cols in district_rows:
            row = parsed_row_from_cols(month, cols)
            entries.extend(collections_from_row(year, row))

    if not found_region_anywhere:
        # Valid district value, but no matching region found in parsed content -> "not found" exception
        raise SourceArgumentNotFound(
            "district",
            district_value,
            message_addition=(
                f"Nie znaleziono danych dla rejonu {region} na stronie. "
                "Możliwe, że rejon nie jest opublikowany lub zmienił się układ strony."
            ),
        )

    if not entries:
        raise Exception(f"Znaleziono rejon {region}, ale nie udało się wyciągnąć żadnych terminów odbioru.")

    uniq = {(e.date, e.type): e for e in entries}
    return sorted(uniq.values(), key=lambda e: (e.date, e.type))


######################################################################
# Source entrypoint
######################################################################
class Source:
    def __init__(self, district: int | str):
        self._district_value = district
        self._district = normalize_district(district)
        _LOGGER.debug("Using district: %s (raw=%r)", self._district, district)

    def fetch(self) -> list[Collection]:
        try:
            soup = fetch_soup()
        except requests.RequestException as e:
            raise Exception(f"Błąd pobierania strony KOM-LUB: {e}") from e

        return scrape_for_region(soup, self._district, self._district_value)