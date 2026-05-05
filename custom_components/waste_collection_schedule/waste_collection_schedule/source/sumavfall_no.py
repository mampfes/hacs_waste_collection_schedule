import datetime
import logging
import urllib.parse

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

_LOGGER = logging.getLogger(__name__)

TITLE = "SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS)"
DESCRIPTION = "Source script for sumavfall.no - Sunnfjord og Ytre Sogn Miljøverk IKS"
URL = "https://www.sumavfall.no"

TEST_CASES = {
    "Blåbærlia 16": {"address": "blåbærlia-16"},
}

ICON_MAP = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple-outline",
    "Papp og plast": "mdi:recycle",
    "Glass og metall": "mdi:glass-fragile",
}

# Typer fra nettsiden som skal slås sammen til én felles type
MERGE_TYPES: dict[str, str] = {
    "Papp/papir": "Papp og plast",
    "Plastemballasje": "Papp og plast",
    "Glas-emballasje": "Glass og metall",
    "Metallemballasje": "Glass og metall",
    # Eldre varianter
    "Papp & Plast": "Papp og plast",
    "Glass- og metallemballasje": "Glass og metall",
}

NORWEGIAN_MONTHS = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address slug as it appears in the URL, e.g. 'blåbærlia-16' or 'storgata-1'",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        normalized_address = urllib.parse.unquote(self._address)
        encoded_address = urllib.parse.quote(normalized_address, safe="-")
        url = f"https://www.sumavfall.no/tommekalender?adresse={encoded_address}"

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HomeAssistant WasteCollectionSchedule)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8",
        }

        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Check if address was found - look for the address heading
        address_heading = soup.find("p", class_="text-3xl")
        if not address_heading or not address_heading.get_text(strip=True):
            raise SourceArgumentNotFoundWithSuggestions(
                argument="address",
                value=self._address,
                suggestions=[],
            )

        entries: list[Collection] = []

        # Each month is a <details> element
        for details in soup.find_all("details"):
            summary = details.find("summary")
            if not summary:
                continue

            month_text = summary.get_text(strip=True).lower()

            # Extract year from the details id, e.g. id="april%202026"
            details_id = details.get("id", "")
            year = None
            try:
                decoded_id = urllib.parse.unquote(details_id)
                # Format: "april 2026"
                parts = decoded_id.strip().split()
                if len(parts) == 2:
                    year = int(parts[1])
            except (ValueError, IndexError):
                pass

            if year is None:
                # Fallback: extract year from month_text
                for part in month_text.split():
                    try:
                        year = int(part)
                        break
                    except ValueError:
                        continue

            if year is None:
                _LOGGER.warning("Could not determine year for month: %s", month_text)
                continue

            # Validate that the summary contains a known month name
            if not any(name in month_text for name in NORWEGIAN_MONTHS):
                _LOGGER.warning("Could not parse month name from: %s", month_text)
                continue

            # Each collection is a <li> inside the details
            for li in details.find_all("li"):
                # Get date text - looks like "08.04.2026"
                date_divs = li.find_all("div", class_=lambda c: c and "flex" in c)
                date_text = None
                for div in date_divs:
                    text = div.get_text(strip=True)
                    # Look for DD.MM.YYYY pattern
                    parts = text.split(".")
                    if len(parts) == 3 and all(p.isdigit() for p in parts):
                        date_text = text
                        break

                if not date_text:
                    # Try to find any text matching date pattern in the li
                    full_text = li.get_text(" ", strip=True)
                    for token in full_text.split():
                        parts = token.split(".")
                        if len(parts) == 3 and all(p.isdigit() for p in parts):
                            date_text = token
                            break

                if not date_text:
                    continue

                try:
                    day, month, yr = date_text.split(".")
                    collection_date = datetime.date(int(yr), int(month), int(day))
                except ValueError:
                    _LOGGER.warning("Could not parse date: %s", date_text)
                    continue

                # Get waste types - each type is in its own <span class="text-lg md:text-2xl">
                waste_spans = li.find_all(
                    "span", class_=lambda c: c and "text-lg" in c and "md:text-2xl" in c
                )
                waste_types = [
                    s.get_text(strip=True)
                    for s in waste_spans
                    if s.get_text(strip=True)
                ]

                if not waste_types:
                    # Fallback: look for any meaningful text in the second div
                    type_divs = li.find_all("div")
                    for div in type_divs:
                        text = div.get_text(strip=True)
                        # Skip date-like strings
                        if "." not in text and len(text) > 2:
                            waste_types = [text]
                            break

                # Merge types and deduplicate (e.g. Glas-emballasje + Metallemballasje -> Glass og metall)
                merged: set[str] = set()
                for waste_type in waste_types:
                    waste_type = waste_type.strip().rstrip(",")
                    if not waste_type:
                        continue
                    merged.add(MERGE_TYPES.get(waste_type, waste_type))

                for waste_type in merged:
                    icon = ICON_MAP.get(waste_type, "mdi:trash-can-outline")
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=waste_type,
                            icon=icon,
                        )
                    )

        if not entries:
            _LOGGER.warning(
                "No collection entries found for address '%s'. "
                "The website structure may have changed.",
                self._address,
            )

        return entries
