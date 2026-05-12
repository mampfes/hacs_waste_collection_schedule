import datetime
import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "ÉTH (Érd, Diósd, Ráckeresztúr, Sóskút, Tárnok)"
DESCRIPTION = "Source script for www.eth-erd.hu"
URL = "https://www.eth-erd.hu"
COUNTRY = "hu"
TEST_CASES = {
    "Test_Erd_Hordo": {"city": "Érd", "street": "Hordó utca"},
    "Test_Diosd_Diofasor": {"city": "Diósd", "street": "Diófasor utca"},
    "Test_Soskut_Ady": {"city": "Sóskút", "street": "Ady Endre utca"},
    "Test_Tarnok_Amur": {"city": "Tárnok", "street": "Amur utca"},
    "Test_Rackeresztur_Ady": {"city": "Ráckeresztúr", "street": "Ady Endre utca"},
}

# Maps lowercase city name to the slug used in the HTML page URL
CITY_SLUG_MAP = {
    "érd": "erd",
    "diósd": "diosd",
    "sóskút": "soskut",
    "tárnok": "tarnok",
    "ráckeresztúr": "rackeresztur",
}

HTML_BASE_URL = "https://www.eth-erd.hu/storage/uploads/{slug}.html"

# CSS classes used in the pre-generated JS calendar and what they mean.
# csakkomm  = communal waste only (no selective on this day)
# kommszel  = communal + selective on the same day
# week<N>   = green (garden) waste, biweekly/monthly route N
# uvegszin  = glass waste (Diósd, Tárnok)
ICON_MAP = {
    "Communal": "mdi:trash-can",
    "Selective": "mdi:recycle",
    "Green": "mdi:leaf",
    "Glass": "mdi:glass-fragile",
}


def _parse_date(date_str: str) -> datetime.date | None:
    """Parse date strings in format 'YYYY-M-D' (no zero-padding)."""
    try:
        parts = date_str.split("-")
        return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


class Source:
    def __init__(self, city: str, street: str = "") -> None:
        self._city = city
        self._street = street

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Resolve city slug
        city_slug = CITY_SLUG_MAP.get(self._city.lower())
        if city_slug is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city", self._city, list(CITY_SLUG_MAP.keys())
            )

        # Fetch the city's HTML page to discover the current telepvegleges JS URL.
        html_url = HTML_BASE_URL.format(slug=city_slug)
        r = session.get(html_url, timeout=30)
        r.raise_for_status()

        # Extract JSDelivr CDN script URLs – the telepvegleges file is the one
        # containing the per-street date assignments.
        cdn_scripts = re.findall(
            r'src="(https://cdn\.jsdelivr\.net/gh/[^"]+telepvegleges[^"]+\.js)"',
            r.text,
        )
        if not cdn_scripts:
            raise SourceArgumentNotFound(
                "city",
                self._city,
                "Could not find the schedule data URL on the provider page.",
            )

        telepvegleges_url = cdn_scripts[0]

        # Fetch the (large) schedule JS file.
        r2 = session.get(telepvegleges_url, timeout=60)
        r2.raise_for_status()
        js_content = r2.text

        # Discover all available street names in this file.
        available_streets = re.findall(r"telep === '([^']+)'", js_content)

        if not available_streets:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No street data found in the provider schedule file.",
            )

        if not self._street:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )

        # Find the block for the requested street.
        escaped = re.escape(self._street)
        block_match = re.search(
            rf"telep === '{escaped}'(.+?)(?=telep === '|\Z)",
            js_content,
            re.DOTALL,
        )
        if block_match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available_streets
            )

        block = block_match.group(1)

        # Extract all addClass assignments: $('#a2026-1-7').addClass('kommszel')
        assignments: dict[str, list[str]] = {}
        for date_str, css_class in re.findall(
            r"'#a(\d{4}-\d+-\d+)'\)\.addClass\('([^']+)'\)", block
        ):
            assignments.setdefault(date_str, []).append(css_class)

        entries: list[Collection] = []
        for date_str, classes in assignments.items():
            d = _parse_date(date_str)
            if d is None:
                continue

            for css_class in classes:
                if css_class == "csakkomm":
                    # Communal waste only
                    entries.append(Collection(d, "Communal", icon=ICON_MAP["Communal"]))
                elif css_class == "kommszel":
                    # Both communal and selective on the same day
                    entries.append(Collection(d, "Communal", icon=ICON_MAP["Communal"]))
                    entries.append(
                        Collection(d, "Selective", icon=ICON_MAP["Selective"])
                    )
                elif re.match(r"week\d+$", css_class) or css_class == "kommzold":
                    # Green (garden) waste
                    entries.append(Collection(d, "Green", icon=ICON_MAP["Green"]))
                    if css_class == "kommzold":
                        # Communal is also collected on these days
                        entries.append(
                            Collection(d, "Communal", icon=ICON_MAP["Communal"])
                        )
                elif css_class == "uvegszin":
                    # Glass waste (Diósd, Tárnok)
                    entries.append(Collection(d, "Glass", icon=ICON_MAP["Glass"]))

        return entries
