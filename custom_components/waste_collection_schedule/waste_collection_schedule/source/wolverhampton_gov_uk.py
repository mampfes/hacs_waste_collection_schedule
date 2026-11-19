import logging
import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

_LOGGER = logging.getLogger(__name__)

TITLE = "Wolverhampton City Council"
DESCRIPTION = "Source for Wolverhampton City Council waste collection."
URL = "https://www.wolverhampton.gov.uk"

TEST_CASES = {
    "Test Case": {"postcode": "WV1 1RD", "uprn": "10094887108"},
}

ICON_MAP = {
    "general_waste": Icons.GENERAL_WASTE,
    "recycling_waste": Icons.RECYCLING,
    "garden_waste": Icons.GARDEN,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def _parse_date(text: str, today: date) -> date:
    """Parse a collection date such as "November 25" or "November 25, 2026".

    The council page used to show "Next date: November 25, 2026" and now shows
    just "November 25". Without a year, assume the next occurrence: a date more
    than a month in the past belongs to next year (December -> January).
    """
    text = re.sub(r"^\s*Next date:\s*", "", text).strip()
    for fmt in ("%B %d, %Y", "%B %d %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    for fmt in ("%B %d", "%d %B"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        result = date(today.year, parsed.month, parsed.day)
        if (today - result).days > 31:
            result = date(today.year + 1, parsed.month, parsed.day)
        return result
    raise ValueError(f"unrecognised date format: {text!r}")


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.replace(" ", "").upper()
        self._uprn = uprn

    def fetch(self):
        # First request to get session cookies
        session = requests.Session()
        session.headers.update(HEADERS)

        # Make the actual request for bin collection data
        url = f"https://www.wolverhampton.gov.uk/find-my-nearest/{self._postcode}/{self._uprn}"

        try:
            r = session.get(url, allow_redirects=True, timeout=30)
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Error fetching data from Wolverhampton Council: {e}"
            ) from e

        soup = BeautifulSoup(r.text, "html.parser")
        entries = []

        # Find the waste containers: the columns under the "Bin collection days"
        # heading. The column class has changed before (col-md-4 -> col-md-3), and
        # matching any col-md-* across the whole page also picks up the
        # councillor and school blocks further down.
        heading = soup.find(
            lambda tag: (
                tag.name in ("h2", "h3")
                and "bin collection days" in tag.get_text(strip=True).lower()
            )
        )
        if heading is None:
            raise Exception(
                "Could not find the 'Bin collection days' section on the Wolverhampton Council page"
            )
        section = heading.find_parent("div") or soup
        waste_containers = section.find_all(
            "div", class_=re.compile(r"^col-(xs|sm|md|lg)-\d+$")
        )
        today = date.today()

        for container in waste_containers:
            waste_type_tag = container.find("h3")
            day_tag = container.find("h4")
            next_date_tag = day_tag.find_next_sibling("h4") if day_tag else None

            if waste_type_tag and day_tag and next_date_tag:
                # Extract waste type and format it
                waste_type_raw = waste_type_tag.text.strip()
                waste_type_key = waste_type_raw.replace(" ", "_").lower()

                # Extract next collection date
                next_date_text = next_date_tag.text.strip()

                try:
                    date_obj = _parse_date(next_date_text, today)

                    # Map the waste type to our standard types for icons
                    if "general" in waste_type_key or "refuse" in waste_type_key:
                        icon_key = "general_waste"
                    elif "recycl" in waste_type_key:
                        icon_key = "recycling_waste"
                    elif "garden" in waste_type_key or "food" in waste_type_key:
                        icon_key = "garden_waste"
                    else:
                        icon_key = waste_type_key

                    entries.append(
                        Collection(
                            date=date_obj,
                            t=waste_type_raw,  # Use the original waste type name
                            icon=ICON_MAP.get(icon_key, "mdi:trash-can"),
                        )
                    )
                except ValueError:
                    _LOGGER.warning(f'parsing of date "{next_date_text}" failed')
                    continue

        return entries
