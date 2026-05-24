"""Source for London Borough of Hillingdon, UK."""

import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "London Borough of Hillingdon"
DESCRIPTION = "Source for London Borough of Hillingdon, UK."
URL = "https://www.hillingdon.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "Property with garden waste subscription, UB10 (Wednesday)": {"uprn": "100021484600"},
    "Property with food waste, UB10 (Wednesday)": {"uprn": "100021484628"},
    "Property with residual waste suffix, UB10 (Tuesday)": {"uprn": "100021484620"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "You need your Unique Property Reference Number (UPRN). An easy way to find it is by going to https://www.findmyaddress.co.uk/ and entering your address details.",
}

PARAM_TRANSLATIONS = {
    "en": {"uprn": "Unique Property Reference Number (UPRN)"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details."
    },
    "de": {
        "uprn": "Eine einfache Möglichkeit, Ihre Unique Property Reference Number (UPRN) zu finden, besteht darin, auf https://www.findmyaddress.co.uk/ zu gehen und Ihre Adressdaten einzugeben."
    },
}

ICON_MAP = {
    "household waste": Icons.GENERAL_WASTE,
    "residual household waste": Icons.GENERAL_WASTE,
    "trade sacks general waste": Icons.COMMERCIAL,
    "dry mixed recycling": Icons.RECYCLING,
    "garden waste": Icons.GARDEN,
    "food waste": Icons.BIO_KITCHEN,
}

API_URL = "https://www.hillingdon.gov.uk/apiserver/ajaxlibrary"
BANK_HOLIDAY_URL = "https://www.hillingdon.gov.uk/bank-holiday-collections"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def _get_icon(waste_type: str) -> Icons | None:
    """Match waste type to icon using case-insensitive keyword matching."""
    lower = waste_type.lower()
    if "recycling" in lower:
        return Icons.RECYCLING
    if "food" in lower:
        return Icons.BIO_KITCHEN
    if "garden" in lower:
        return Icons.GARDEN
    if "trade" in lower:
        return Icons.COMMERCIAL
    if "waste" in lower:
        return Icons.GENERAL_WASTE
    return ICON_MAP.get(lower)


def _strip_suffix(waste_type: str) -> str:
    """Strip parenthetical suffixes like ' ( - 31/05/2026 23:59)' or ' ( - )'."""
    return re.sub(r"\s*\(.*?\)\s*$", "", waste_type).strip()


def _fetch_bank_holiday_substitutions() -> dict[date, date]:
    """Fetch the bank holiday table and return a mapping of normal date -> revised date."""
    substitutions: dict[date, date] = {}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        r = requests.get(BANK_HOLIDAY_URL, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return substitutions

        today = date.today()

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            normal_text = cells[0].get_text(strip=True)
            revised_text = cells[1].get_text(strip=True)

            # Strip parenthetical like "(Bank Holiday)"
            normal_text = re.sub(r"\s*\(.*?\)", "", normal_text).strip()

            # Parse dates - they don't include year
            try:
                normal_dt = datetime.strptime(normal_text, "%A %d %B")
                revised_dt = datetime.strptime(revised_text, "%A %d %B")
            except ValueError:
                continue

            # Assign year: use current year, but if date has passed, use next year
            normal_date = normal_dt.replace(year=today.year).date()
            if normal_date < today - timedelta(days=30):
                normal_date = normal_date.replace(year=today.year + 1)

            revised_date = revised_dt.replace(year=normal_date.year).date()

            substitutions[normal_date] = revised_date

    except Exception:
        # Silently skip if page unavailable
        pass

    return substitutions


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "Hillingdon.DatasourceQueries.alloy.GetBinCollectionDay",
            "params": {"UPRN": self._uprn},
        }
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://www.hillingdon.gov.uk/article/1171/Look-up-my-collection-day",
        }

        r = requests.post(API_URL, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

        result = data.get("result", {})
        if not result.get("success"):
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data found for this UPRN. Please verify it is correct.",
            )

        collection_day = result.get("collectionDay", "")
        waste_types = result.get("collection", [])

        if not collection_day or collection_day not in WEEKDAYS:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                f"Invalid collection day returned: '{collection_day}'",
            )

        # Fetch bank holiday substitutions
        substitutions = _fetch_bank_holiday_substitutions()

        # Generate next 8 weekly occurrences of the collection day
        target_weekday = WEEKDAYS[collection_day]
        today = date.today()
        days_ahead = (target_weekday - today.weekday()) % 7
        if days_ahead == 0:
            # Include today if it's the collection day
            next_date = today
        else:
            next_date = today + timedelta(days=days_ahead)

        collection_dates = []
        for i in range(8):
            d = next_date + timedelta(weeks=i)
            # Apply bank holiday substitution if applicable
            if d in substitutions:
                d = substitutions[d]
            collection_dates.append(d)

        # Build Collection entries
        entries: list[Collection] = []
        for waste_type_raw in waste_types:
            waste_type = _strip_suffix(waste_type_raw)
            icon = _get_icon(waste_type)
            for d in collection_dates:
                entries.append(Collection(date=d, t=waste_type, icon=icon))

        return entries
