import datetime
import difflib
import json
import re
from urllib.parse import urljoin

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Gelbe Tonne München-Ost (Knettenbrech + Gurdulic)"
DESCRIPTION = "Source for the Gelbe Tonne (yellow bin) collection in the eastern part of Munich, operated by Knettenbrech + Gurdulic on behalf of the Dual Systems."
URL = "https://www.gelbe-tonne-muenchen-ost.de"
COUNTRY = "de"
SOURCE_CODEOWNERS = ["@OnSerious"]
TEST_CASES = {
    "Aachener Str. (whole street)": {"street": "Aachener Str."},
    "Balanstr. (house number range)": {
        "street": "Balanstr.",
        "house_number": "53-Ende, 48-Ende",
    },
    "Chiemgaustr. (house number range)": {
        "street": "Chiemgaustr.",
        "house_number": "109-Ende, 114-Ende",
    },
}

WASTE_TYPE = "Gelbe Tonne"
ICON_MAP = {WASTE_TYPE: Icons.PLASTIC_PACKAGING}

CALENDAR_PAGE = "https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender"
COMPLETE = "Komplett"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street exactly as listed on https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender (e.g. 'Balanstr.'). A house number is only needed for streets that are split between collection districts; if it is missing, the form offers the valid house number ranges.",
    "de": "Straße genau so eingeben wie auf https://www.gelbe-tonne-muenchen-ost.de/abfuhrkalender (z.B. 'Balanstr.'). Eine Hausnummer ist nur für Straßen nötig, die auf mehrere Abfuhrbezirke aufgeteilt sind; fehlt sie, bietet das Formular die gültigen Hausnummernbereiche zur Auswahl an.",
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street", "house_number": "House number"},
    "de": {"street": "Straße", "house_number": "Hausnummer"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name as used on the provider website, e.g. 'Balanstr.'",
        "house_number": "Only required for split streets: a house number (e.g. '12') or a range exactly as shown on the website (e.g. '53-Ende, 48-Ende')",
    },
    "de": {
        "street": "Straßenname wie auf der Website des Entsorgers, z.B. 'Balanstr.'",
        "house_number": "Nur bei geteilten Straßen nötig: Hausnummer (z.B. '12') oder Bereich genau wie auf der Website (z.B. '53-Ende, 48-Ende')",
    },
}

# The website is a Vue app that ships all data inside one JavaScript bundle:
#  - a CSV "Bezirk;Straße;Bemerkung" mapping streets (and house number ranges) to districts
#  - an iCalendar whose events carry the district number as SUMMARY
_CSV_RE = re.compile(r'"(Bezirk;Stra(?:[^"\\]|\\.)*)"')
_ICS_RE = re.compile(r'"(BEGIN:VCALENDAR(?:[^"\\]|\\.)*)"')
_SCRIPT_RE = re.compile(r'<script[^>]+src="([^"]*abfuhrkalender[^"]*\.js[^"]*)"', re.I)
_HN_RE = re.compile(r"^\s*(\d+)\s*([a-z]?)\s*$", re.I)


def _normalize_street(street: str) -> str:
    s = street.lower().strip()
    s = s.replace("straße", "str.").replace("strasse", "str.")
    return re.sub(r"[\s.\-]", "", s)


def _parse_hn(value: str) -> tuple[int, str] | None:
    m = _HN_RE.match(value)
    if not m:
        return None
    return int(m.group(1)), m.group(2).lower()


def _range_matches(spec: str, hn: tuple[int, str]) -> bool:
    """Check a house number against a spec like '1-51, 2-46', '25c-Ende' or '8'.

    Each comma-separated part is one side of the street: its parity is taken
    from the first number (odd/even), the upper bound may be 'Ende'.
    """
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lower, _, upper = part.partition("-")
        start = _parse_hn(lower)
        if start is None:
            continue
        if not upper:
            if hn[0] == start[0] and (not start[1] or hn[1] == start[1]):
                return True
            continue
        if hn[0] % 2 != start[0] % 2:
            continue
        if hn < start:
            continue
        end = _parse_hn(upper)
        if end is None:
            # open-ended: "Ende" (the provider data also contains it misspelt once)
            return True
        if hn[0] < end[0] or (hn[0] == end[0] and hn[1] <= (end[1] or "z")):
            return True
    return False


class Source:
    def __init__(self, street: str, house_number: str | int | None = None):
        self._street = street
        self._house_number = (
            str(house_number).strip() if house_number not in (None, "") else ""
        )

    def _load_bundle(self) -> str:
        page = requests.get(CALENDAR_PAGE, timeout=30)
        page.raise_for_status()
        m = _SCRIPT_RE.search(page.text)
        if not m:
            raise Exception("Calendar script not found on provider website")
        js = requests.get(urljoin(CALENDAR_PAGE, m.group(1)), timeout=60)
        js.raise_for_status()
        return js.text

    @staticmethod
    def _decode(regex: re.Pattern, js: str, marker: str, what: str) -> str:
        # The bundle also contains short literals (e.g. "BEGIN:VCALENDAR" in the
        # ICS export code), so pick the largest literal that holds real data.
        candidates = [
            json.loads(f'"{m.group(1)}"')
            for m in regex.finditer(js)
            if marker in m.group(1)
        ]
        if not candidates:
            raise Exception(f"{what} not found in provider calendar script")
        return max(candidates, key=len)

    def _find_district(self, rows: list[tuple[int, str, str]]) -> int:
        streets = sorted({r[1] for r in rows})
        matches = [r for r in rows if r[1] == self._street]
        if not matches:
            wanted = _normalize_street(self._street)
            matches = [r for r in rows if _normalize_street(r[1]) == wanted]
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                difflib.get_close_matches(self._street, streets, n=10, cutoff=0.6)
                or streets,
            )

        if len(matches) == 1 and matches[0][2] == COMPLETE:
            return matches[0][0]

        specs = [r[2] for r in matches]
        if not self._house_number:
            raise SourceArgumentRequiredWithSuggestions(
                "house_number",
                "This street is split between collection districts",
                specs,
            )
        for district, _, spec in matches:
            if spec == self._house_number:
                return district
        hn = _parse_hn(self._house_number)
        if hn is not None:
            hits = [r for r in matches if r[2] == COMPLETE or _range_matches(r[2], hn)]
            if len({r[0] for r in hits}) == 1:
                return hits[0][0]
            if hits:
                # the provider data assigns some numbers to two districts
                raise SourceArgAmbiguousWithSuggestions(
                    "house_number", self._house_number, [r[2] for r in hits]
                )
        raise SourceArgumentNotFoundWithSuggestions(
            "house_number", self._house_number, specs
        )

    def fetch(self) -> list[Collection]:
        js = self._load_bundle()
        csv = self._decode(_CSV_RE, js, "\\n", "Street list")
        ics = self._decode(_ICS_RE, js, "BEGIN:VEVENT", "Collection calendar")

        rows: list[tuple[int, str, str]] = []
        for line in csv.lstrip("﻿").splitlines()[1:]:
            parts = [p.strip() for p in line.split(";")]
            if len(parts) == 3 and parts[0].isdigit() and parts[1]:
                rows.append((int(parts[0]), parts[1], parts[2]))
        if not rows:
            raise Exception("Street list from provider is empty")

        district = self._find_district(rows)

        dates: set[datetime.date] = set()
        for event in re.findall(r"BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT", ics, re.S):
            summary = re.search(r"^SUMMARY:(\d+)\s*$", event, re.M)
            start = re.search(r"^DTSTART(?:;[^:]*)?:(\d{8})", event, re.M)
            if summary and start and int(summary.group(1)) == district:
                dates.add(datetime.datetime.strptime(start.group(1), "%Y%m%d").date())
        if not dates:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                f"No collection dates found for district {district}",
            )

        return [
            Collection(date=d, t=WASTE_TYPE, icon=ICON_MAP.get(WASTE_TYPE))
            for d in sorted(dates)
        ]
