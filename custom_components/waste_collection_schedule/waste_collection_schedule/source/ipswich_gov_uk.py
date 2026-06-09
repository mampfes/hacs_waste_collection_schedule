import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Ipswich Borough Council"
DESCRIPTION = (
    "Source for waste collection schedules provided by Ipswich Borough Council, UK."
)
URL = "https://www.ipswich.gov.uk"
COUNTRY = "uk"

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://app.ipswich.gov.uk/bin-collection-better-recycling/ and search "
        "for your street. Once your schedule is displayed the URL will end with "
        "/weeks/<number> — use that number as the `location_id` argument."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "location_id": (
            "Numeric location ID from the end of the schedule URL. "
            "Example: for …/weeks/549 use location_id: 549."
        ),
    },
}

TEST_CASES = {
    "High Street (id 549)": {"location_id": 549},
}

_SCHEDULE_URL = "https://app.ipswich.gov.uk/bin-collection-better-recycling/months/{}"

# Map keywords found in <dt> text to a canonical display name and MDI icon.
# Evaluated in order; first match wins.
_BIN_MAP: list[tuple[str, str, str]] = [
    ("food", "Food Waste", "mdi:food-apple"),
    ("black", "General Waste", "mdi:trash-can"),
    ("blue", "Recycling (Blue bin)", "mdi:recycle"),
    ("green", "Recycling (Green bin)", "mdi:recycle"),
    ("brown", "Garden Waste", "mdi:leaf"),
]

# Strips ordinal suffixes so "4th" → 4, "22nd" → 22, etc.
_ORDINAL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)", re.IGNORECASE)

# Matches "<Month> <Year>" headings produced by <h4> elements.
_MONTH_HEADING_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{4})$",
    re.IGNORECASE,
)

_MONTH_NAMES: dict[str, int] = {
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


def _classify(dt_text: str) -> tuple[str, str]:
    """Return (display_name, icon) for a <dt> bin description."""
    lower = dt_text.lower()
    for keyword, name, icon in _BIN_MAP:
        if keyword in lower:
            return name, icon
    return dt_text.strip().title(), "mdi:trash-can"


def _parse_days(dd_text: str) -> list[int]:
    """Parse a comma-separated ordinal list, e.g. '4th, 11th, 18th' → [4, 11, 18]."""
    return [int(m.group(1)) for m in _ORDINAL_RE.finditer(dd_text)]


class Source:
    def __init__(self, location_id: int | str) -> None:
        self._location_id = int(location_id)

    def fetch(self) -> list[Collection]:
        url = _SCHEDULE_URL.format(self._location_id)
        response = requests.get(url, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                raise SourceArgumentNotFound(
                    "location_id",
                    self._location_id,
                ) from exc
            raise

        soup = BeautifulSoup(response.text, "html.parser")

        # The relevant page structure inside <article>:
        #
        #   <h4>June 2026</h4>
        #   <dl class="ibc-columns ibc-zebra">
        #     <dt>Large food waste caddy</dt>  <dd>4th, 11th, 18th, 25th</dd>
        #     <dt>Black refuse bin</dt>         <dd>11th, 25th</dd>
        #     <dt>Blue recycling bin</dt>       <dd>4th</dd>
        #     …
        #   </dl>
        #   <h4>July 2026</h4>
        #   <dl …> … </dl>
        #
        # We walk all <h4> and <dl> siblings in document order, tracking the
        # current month/year from each <h4> and emitting Collections for each
        # <dt>/<dd> pair in the following <dl>.

        article = soup.find("article")
        if article is None:
            raise SourceArgumentNotFound("location_id", self._location_id)

        collections: list[Collection] = []
        current_month: int | None = None
        current_year: int | None = None

        for element in article.find_all(["h4", "dl"]):
            if element.name == "h4":
                m = _MONTH_HEADING_RE.match(element.get_text(strip=True))
                if m:
                    current_month = _MONTH_NAMES[m.group(1).lower()]
                    current_year = int(m.group(2))

            elif element.name == "dl":
                if current_month is None or current_year is None:
                    continue  # <dl> before any recognisable month heading

                for dt, dd in zip(element.find_all("dt"), element.find_all("dd")):
                    bin_name, icon = _classify(dt.get_text(strip=True))
                    for day in _parse_days(dd.get_text(strip=True)):
                        try:
                            collection_date = date(current_year, current_month, day)
                        except ValueError:
                            continue  # guard against malformed day numbers
                        collections.append(
                            Collection(date=collection_date, t=bin_name, icon=icon)
                        )

        if not collections:
            raise SourceArgumentNotFound("location_id", self._location_id)

        return collections
