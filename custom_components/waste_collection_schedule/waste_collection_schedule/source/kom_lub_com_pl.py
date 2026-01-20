from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup, Tag

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentRequired,
)

TITLE = "KOM-LUB (Luboń, PL)"
DESCRIPTION = "Scrapes waste collection schedule by district (1..7) from kom-lub.com.pl."
URL = "https://kom-lub.com.pl/aktualny-harmonogram-wywozow/"

#########################################################################

TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestDistrict1": {"district": 1},
    "TestDistrict2": {"district": 2},
    "TestDistrict3": {"district": 3},
    "TestDistrict4": {"district": 4},
    "TestDistrict5": {"district": 5},
    "TestDistrict6": {"district": 6},
    "TestDistrict7": {"district": 7},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "pl": """
1) Wejdź na stronę harmonogramu:
https://kom-lub.com.pl/alfabetyczny-wykaz-ulic-i-rejony/

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

#########################################################################


# Toggle debugging here
DEBUG = False


def dbg(msg: str) -> None:
    if DEBUG:
        print(f"[DEBUG] {msg}")


# -------------------------
# Icons (Home Assistant MDI)
# -------------------------
ICON_BY_TYPE: dict[str, str] = {
    "Mixed": "mdi:trash-can",
    "Glass": "mdi:glass-wine",
    "Plastics": "mdi:recycle",
    "Paper": "mdi:newspaper-variant-multiple",
    "Bulky": "mdi:sofa",
    "Bio": "mdi:leaf",
}

# -------------------------
# District normalization
# -------------------------
_DISTRICT_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}


def normalize_district(district: int | str) -> str:
    """Accepts 1..7 (int/str) and returns 'R I' .. 'R VII'."""
    if district is None or str(district).strip() == "":
        # required argument missing
        raise SourceArgumentRequired("district")

    try:
        n = int(district)
    except Exception:
        # invalid type/value for that argument
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


# -------------------------
# Parsing helpers
# -------------------------
_ROMAN_MONTH = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
    "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
}

_REGION_RE = re.compile(r"^R\s*[IVX]+$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedRow:
    month: int
    mixed: List[int]
    glass: List[int]
    plastics: List[int]
    paper: List[int]
    bulky: List[int]
    bio: List[int]


COL_NAMES = ["Mixed", "Glass", "Plastics", "Paper", "Bulky", "Bio"]


def safe_date(y: int, m: int, d: int) -> Optional[dt.date]:
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def extract_day_numbers(text: str) -> List[int]:
    """Robust: pull any 1-2 digit numbers from the cell."""
    return [int(x) for x in re.findall(r"\d{1,2}", text or "")]


# -------------------------
# HTML fetching
# -------------------------
def fetch_soup() -> BeautifulSoup:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.content, "html.parser")


def extract_tables(soup: BeautifulSoup) -> dict[str, Tag]:
    """
    Finds all quarter tables and returns: {title: <table>}
    Where title is like: "II kwartał 2025"
    """
    result: dict[str, Tag] = {}

    entry_content = soup.find_all("div", {"class": "entry-content"})[0]
    divs = entry_content.find_all("div")

    for i, div in enumerate(divs):
        strong = div.find("strong", recursive=False)
        if not strong:
            continue

        text = strong.get_text(strip=True)
        if not text.startswith("Harmonogram wywozów"):
            continue

        # title after the dash
        title = text.split("–", 1)[1].strip()

        # next table in following divs
        for next_div in divs[i + 1:]:
            table = next_div.find("table")
            if table:
                result[title] = table
                break

    dbg(f"Found {len(result)} tables: {list(result.keys())}")
    return result


def parse_quarter_key(title: str) -> tuple[str, int]:
    """
    More robust: find quarter roman and 4-digit year anywhere in the title.
    """
    q_map = {"I": 1, "II": 2, "III": 3, "IV": 4}

    m_q = re.search(r"\b(I|II|III|IV)\b", title)
    m_y = re.search(r"\b(20\d{2})\b", title)

    if not m_q or not m_y:
        raise ValueError(f"Cannot parse quarter/year from title: {title!r}")

    return (m_y.group(1), q_map[m_q.group(1)])


# -------------------------
# Table parsing
# -------------------------
def extract_month_row(tr: Tag) -> dict[int, list[list[int]]]:
    """
    Returns {month: cols} where cols are 6 columns [mixed, glass, plastics, paper, bulky, bio]

    IMPORTANT:
    We expand td colspans, because rows with empty middle columns can be
    represented by fewer <td> cells in HTML.
    """
    month_token = tr.find("th").get_text(strip=True).upper()
    month = _ROMAN_MONTH.get(month_token)
    if not month:
        raise ValueError(f"Unexpected month token: {month_token!r}")

    tds = tr.find_all("td")

    # Debug raw HTML cell count
    if DEBUG:
        dbg(f"Month {month_token} -> raw td count: {len(tds)}")

    cols: list[list[int]] = []
    for td in tds:
        text = td.get_text(" ", strip=True)
        days = extract_day_numbers(text)
        colspan = int(td.get("colspan", 1) or 1)

        # If cell is empty text, treat it as empty list even if "days" is empty anyway
        value = days if text else []

        # Expand colspan
        for _ in range(colspan):
            cols.append(value)

    # Normalize to exactly 6 columns
    if len(cols) != 6:
        dbg(f"Month {month_token}: after colspan expansion cols={len(cols)} (expected 6). cols={cols}")

    while len(cols) < 6:
        cols.append([])
    cols = cols[:6]

    return {month: cols}


def split_table_by_district(table: Tag) -> dict[str, list[dict[int, list[list[int]]]]]:
    """
    Returns: { 'R I': [ {4: cols}, {5: cols}, ... ], 'R II': [...], ... }
    """
    district_rows: dict[str, list[dict[int, list[list[int]]]]] = {}
    cur_district: str | None = None

    # 1) Try to read the very first district label from THEAD (some tables put R I there)
    thead = table.find("thead")
    if thead:
        header_tr = thead.find("tr")
        if header_tr:
            first_th = header_tr.find("th")
            if first_th:
                th_text = first_th.get_text(" ", strip=True).upper().replace("  ", " ").strip()
                if _REGION_RE.match(th_text):
                    cur_district = th_text
                    district_rows.setdefault(cur_district, [])
                    dbg(f"Initial district from THEAD: {cur_district}")

    # 2) Parse TBODY rows
    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("No tbody found")

    for tr in tbody.find_all("tr", recursive=False):
        first_th = tr.find("th")
        if not first_th:
            continue

        th_text = first_th.get_text(" ", strip=True).upper().replace("  ", " ").strip()

        # district header in TBODY
        if _REGION_RE.match(th_text):
            cur_district = th_text
            district_rows.setdefault(cur_district, [])
            continue

        # month row
        if cur_district is None:
            # If the site doesn't include "R I" label anywhere, assume first block is R I
            cur_district = "R I"
            district_rows.setdefault(cur_district, [])
            dbg("No district header found before month rows; defaulting to R I")

        district_rows[cur_district].append(extract_month_row(tr))

    return district_rows


def parse_tables_dict(tables_by_title: dict[str, Tag]) -> dict[
    tuple[str, int], dict[str, list[dict[int, list[list[int]]]]]]:
    """
    (year_str, quarter) -> (district -> list of month dicts)
    """
    out: dict[tuple[str, int], dict[str, list[dict[int, list[list[int]]]]]] = {}

    for title, table in tables_by_title.items():
        key = parse_quarter_key(title)
        out[key] = split_table_by_district(table)
        dbg(f"Parsed table {title!r} -> key={key} districts={list(out[key].keys())}")

    return out


# -------------------------
# Conversion to Collections
# -------------------------
def parsed_row_from_cols(month: int, cols: list[list[int]]) -> ParsedRow:
    # cols already normalized to 6 in extract_month_row
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

    def add(days: list[int], name: str) -> None:
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


def scrape_for_region(soup: BeautifulSoup, region: str) -> list[Collection]:
    tables = extract_tables(soup)
    if not tables:
        raise Exception("Nie znaleziono tabel harmonogramu na stronie (zmienił się układ strony?).")

    sections = parse_tables_dict(tables)
    if not sections:
        raise Exception("Nie udało się sparsować tabel harmonogramu (brak danych po parsowaniu).")

    entries: list[Collection] = []
    found_region_anywhere = False

    for (year_str, quarter), regions in sections.items():
        district_rows = regions.get(region)
        if district_rows:
            found_region_anywhere = True
        else:
            continue

        year = int(year_str)
        dbg(f"Collecting for {region} year={year} quarter={quarter}, month_rows={len(district_rows)}")

        for month_map in district_rows:
            for month, cols in month_map.items():
                row = parsed_row_from_cols(month, cols)
                entries.extend(collections_from_row(year, row))

    if not found_region_anywhere:
        # argument "district" is valid 1..7, but the page does not contain that region => show error on field
        raise SourceArgumentException(
            "district",
            f"Nie znaleziono danych dla rejonu {region} na stronie. "
            f"Możliwe, że zmienił się układ tabel lub rejon nie jest opublikowany.",
        )

    if not entries:
        # Region was present, but there are no pickup dates (shouldn't happen) => treat as parsing/site issue
        raise Exception(f"Znaleziono rejon {region}, ale nie udało się wyciągnąć żadnych terminów odbioru.")

    uniq = {(e.date, e.type): e for e in entries}
    return sorted(uniq.values(), key=lambda e: (e.date, e.type))


# -------------------------
# Pretty printing / debugging helpers
# -------------------------
def fmt_days(days: list[int]) -> str:
    return "-" if not days else ", ".join(str(d) for d in days)


def print_district_quarter_table(
        sections: dict[tuple[str, int], dict[str, list[dict[int, list[list[int]]]]]],
        year: int,
        quarter: int,
        district: str,
) -> None:
    """
    Prints a readable table for one quarter + district.
    """
    key = (str(year), quarter)
    regions = sections.get(key)
    if not regions:
        print(f"No data for {key}")
        return

    rows = regions.get(district)
    if not rows:
        print(f"No data for district {district} in {key}")
        return

    print()
    print(f"== {district} | {year} Q{quarter} ==")
    header = ["Month"] + COL_NAMES
    widths = [5] + [14] * 6

    def print_line(cols: list[str]) -> None:
        print(" | ".join(c.ljust(w) for c, w in zip(cols, widths)))

    print_line(header)
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    for month_map in rows:
        for month, cols in month_map.items():
            line = [str(month)]
            for i in range(6):
                line.append(fmt_days(cols[i]))
            print_line(line)

    print()


# -------------------------
# Source entrypoint
# -------------------------
class Source:
    def __init__(self, district: int | str):
        self._district = normalize_district(district)
        dbg(f"user provided: {self._district}")

    def fetch(self) -> list[Collection]:
        try:
            soup = fetch_soup()
        except requests.RequestException as e:
            raise Exception(f"Błąd pobierania strony KOM-LUB: {e}") from e

        return scrape_for_region(soup, self._district)

#
# if __name__ == "__main__":
#     # Example run
#     district = normalize_district(1)
#     soup = fetch_soup()
#
#     tables = extract_tables(soup)
#     sections = parse_tables_dict(tables)
#
#     # Pretty print all quarters for district 1:
#     for (y, q) in sorted(sections.keys()):
#         print_district_quarter_table(sections, int(y), q, district)
#
#     # And also print final collections:
#     entries = scrape_for_region(soup, district)
#     dbg(f"Got {len(entries)} entries")
#     for e in entries:
#         dbg(f"{e.date}, {e.t}, {e.icon}")
