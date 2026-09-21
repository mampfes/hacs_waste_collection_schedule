import json
import re
import unicodedata
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "AKSD Debrecen"
DESCRIPTION = (
    "Source for waste collection in Debrecen, Hungary, provided by A.K.S.D. Kft."
)
URL = "https://www.aksd.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Kinizsi utca": {"street": "Kinizsi utca"},
    "Ábel utca": {"street": "Ábel utca"},
    "Abigél utca (no accents)": {"street": "abigel utca"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter the street name exactly as it appears in the street search at https://www.aksd.hu/hulladeknaptar (e.g. `Kinizsi utca`). Upper/lower case and accents are ignored.",
    "de": "Geben Sie den Straßennamen genau so ein, wie er in der Straßensuche auf https://www.aksd.hu/hulladeknaptar erscheint (z. B. `Kinizsi utca`). Groß-/Kleinschreibung und Akzente werden ignoriert.",
}

PARAM_DESCRIPTIONS = {
    "en": {"street": "Street name, e.g. `Kinizsi utca`"},
    "de": {"street": "Straßenname, z. B. `Kinizsi utca`"},
}

PARAM_TRANSLATIONS = {
    "en": {"street": "Street"},
    "de": {"street": "Straße"},
}

ICON_MAP = {
    "black": Icons.GENERAL_WASTE,
    "yellow": Icons.RECYCLING,
    "brown": Icons.GARDEN,
    "green": Icons.GARDEN,
    "lockable": Icons.BIO_KITCHEN,
}

NAME_MAP = {
    "black": "General waste",
    "yellow": "Recycling",
    "brown": "Garden waste (bin)",
    "green": "Garden waste (bag)",
    "lockable": "Food waste",
}

# Garden waste (brown bin and green bag) is only collected from March to December.
SEASONAL_TYPES = {"brown", "green"}
SEASON_MONTHS = range(3, 13)

# Only Debrecen is served by this calendar. Any Debrecen zip code returns the same
# street list, the site merely requires a valid one to be stored in the session.
ZIP_CODE = "4024"
CALENDAR_URL = "https://www.aksd.hu/hulladeknaptar"
ZIP_URL = "https://www.aksd.hu/ajax/save_customer_zip"

WEEKDAYS = {
    "hetfo": 0,
    "kedd": 1,
    "szerda": 2,
    "csutortok": 3,
    "pentek": 4,
    "szombat": 5,
    "vasarnap": 6,
}

DAYS_AHEAD = 366


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(c for c in text if not unicodedata.combining(c))


def _parse_rule(text: str) -> tuple[bool, set[int]]:
    """Return (odd_weeks_only, weekdays) for a text such as
    "Csütörtök" or "Minden páratlan héten kedd vagy péntek"."""
    norm = _normalize(text)
    odd_only = "paratlan" in norm
    days = {WEEKDAYS[w] for w in re.findall(r"[a-z]+", norm) if w in WEEKDAYS}
    return odd_only, days


class Source:
    def __init__(self, street: str):
        self._street = street

    def _get_streets(self) -> list[dict]:
        session = requests.Session()
        r = session.get(CALENDAR_URL, timeout=30)
        r.raise_for_status()
        r = session.post(
            ZIP_URL,
            data={"zip": ZIP_CODE, "type": "residential", "close": "false"},
            timeout=30,
        )
        r.raise_for_status()
        r = session.get(CALENDAR_URL, timeout=30)
        r.raise_for_status()

        match = re.search(r"const wasteCalendarStreets = (\[.*?\]);\s*\n", r.text)
        if not match:
            raise Exception("Could not find street data on the AKSD calendar page")
        return json.loads(match.group(1))

    def fetch(self) -> list[Collection]:
        streets = self._get_streets()

        wanted = _normalize(self._street)
        street = next(
            (
                s
                for s in streets
                if wanted == _normalize(s["label"])
                or wanted in [_normalize(v) for v in s.get("searchValues", [])]
            ),
            None,
        )
        if street is None:
            suggestions = sorted(
                {
                    s["label"]
                    for s in streets
                    if wanted and wanted in _normalize(s["label"])
                }
            )
            if suggestions:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street", self._street, suggestions[:20]
                )
            raise SourceArgumentNotFound("street", self._street)

        today = date.today()
        entries: list[Collection] = []
        for bin_type, rules in street["options"].items():
            for rule in rules:
                odd_only, weekdays = _parse_rule(rule)
                if not weekdays:
                    continue
                for offset in range(DAYS_AHEAD):
                    day = today + timedelta(days=offset)
                    if day.weekday() not in weekdays:
                        continue
                    if odd_only and day.isocalendar()[1] % 2 == 0:
                        continue
                    if bin_type in SEASONAL_TYPES and day.month not in SEASON_MONTHS:
                        continue
                    entries.append(
                        Collection(
                            date=day,
                            t=NAME_MAP.get(bin_type, bin_type),
                            icon=ICON_MAP.get(bin_type),
                        )
                    )
        return entries
