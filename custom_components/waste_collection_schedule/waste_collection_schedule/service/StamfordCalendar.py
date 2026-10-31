"""Stamford's public street lookup and house-number-range tables."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import Parser

BASE_URL = "https://stamfordapps.org/garbagerecycling/"
RANGE_RE = re.compile(r"(\d+)(?:\s*TO\s*(\d+))?\s*(BOTH|ODD|EVEN)?")
WEEKDAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def street_url(response, street, **_):
    soup = BeautifulSoup(response.text, "html.parser")
    matches: dict[str, str] = {}
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "StreetResultsDetails.asp" not in href:
            continue
        row = link.find_parent("tr")
        name_cell = row.find_all("td")[0] if row is not None else None
        name = (
            name_cell.get_text(strip=True)
            if name_cell is not None
            else link.get_text(strip=True)
        )
        matches[name] = urljoin(BASE_URL, str(href))
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            argument="street", value=street, suggestions=[]
        )
    if len(matches) == 1:
        return next(iter(matches.values()))
    upper_query = street.upper()
    exact = [name for name in matches if name == upper_query]
    if len(exact) == 1:
        return matches[exact[0]]
    starts_with = [name for name in matches if name.startswith(upper_query + " ")]
    if len(starts_with) == 1:
        return matches[starts_with[0]]
    raise SourceArgAmbiguousWithSuggestions(
        argument="street", value=street, suggestions=sorted(matches.keys())
    )


def _find_section_table(soup: BeautifulSoup, label: str):
    for table in reversed(soup.select("table table")):
        text = table.get_text(" ", strip=True).upper()
        if f"{label} PICKUP INFORMATION" in text:
            return table
    return None


def _iter_rows(table):
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 3:
            continue
        range_text = cells[0].get_text(" ", strip=True)
        if range_text.upper() == "ALL":
            yield 0, float("inf"), "BOTH", cells[2].get_text(" ", strip=True).upper()
            continue
        if not any(ch.isdigit() for ch in range_text):
            continue
        match = RANGE_RE.search(range_text.upper())
        if not match:
            continue
        low = int(match.group(1))
        high = int(match.group(2)) if match.group(2) else low
        parity = match.group(3) or "BOTH"
        day_text = cells[2].get_text(" ", strip=True).upper()
        yield (low, high, parity, day_text)


def determine_day(table, waste_type: str, street, house_number) -> str | None:
    rows = list(_iter_rows(table))
    if not rows:
        return None

    def describe(row):
        low, high, parity, day_text = row
        return f"{low}-{high} ({parity.lower()}): {day_text.title()}"

    if house_number is not None:
        matching = [
            day_text
            for low, high, parity, day_text in rows
            if low <= house_number <= high
            and (
                parity == "BOTH"
                or (parity == "ODD" and house_number % 2 == 1)
                or (parity == "EVEN" and house_number % 2 == 0)
            )
        ]
        if not matching:
            raise SourceArgumentNotFoundWithSuggestions(
                argument="house_number",
                value=house_number,
                suggestions=[describe(row) for row in rows],
            )
        day_text = matching[0]
    else:
        distinct = {row[3] for row in rows}
        if len(distinct) > 1:
            raise SourceArgumentRequiredWithSuggestions(
                argument="house_number",
                reason=f"{waste_type} pickup day varies by house number on {street}",
                suggestions=[describe(row) for row in rows],
            )
        day_text = rows[0][3]
    if day_text not in WEEKDAYS:
        if day_text in ("NO GARBAGE PICKUP", "NO RECYCLING PICKUP"):
            return None
        raise ValueError(f"Unrecognized Stamford pickup day: {day_text!r}")
    return day_text


class CalendarParser(Parser[list[dict]]):
    def __call__(self, response, source=None):
        if source is None:
            raise ValueError("Stamford lookup requires a source")
        street = source.params["street"]
        number = source.params.get("house_number")
        if number not in (None, ""):
            try:
                number = int(str(number).strip())
            except ValueError:
                raise SourceArgumentNotFound(
                    "house_number",
                    number,
                    message_addition="house_number must be a whole number.",
                ) from None
        else:
            number = None
        soup = BeautifulSoup(response.text, "html.parser")
        records = []
        for label, key in (("RECYCLING", "recycling"), ("GARBAGE", "general")):
            table = _find_section_table(soup, label)
            if table is None:
                raise ValueError(f"Missing Stamford {label.lower()} table")
            day = determine_day(table, label, street, number)
            if day:
                records.append({"day": day, "type": key})
        if not records:
            raise SourceArgumentNotFound(
                "street",
                street,
                message_addition="No residential garbage or recycling pickup for this street.",
            )
        return records
