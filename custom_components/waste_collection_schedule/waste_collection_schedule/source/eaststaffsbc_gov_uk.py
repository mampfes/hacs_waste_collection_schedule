import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "East Staffordshire Borough Council"
DESCRIPTION = "Source for East Staffordshire Borough Council"
URL = "https://www.eaststaffsbc.gov.uk/"
TEST_CASES = {
    "Marlpit Lane": {"uid": 103368},
    "Church Lane": {"uid": "103281"},
}
ICON_MAP = {
    "Blue Bin": "mdi:recycle",
    "Brown Bin": "mdi:leaf",
    "Weekly Food Waste": "mdi:food",
    "Blue Bag": "mdi:newspaper",
    "Grey Bin": "mdi:trash-can",
}
API_URL = "https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates"


def parse_date_with_rollover(date_str, last_date=None):
    """
    Convert 'Tuesday, 21st April' -> datetime.date.

    Handle year-end rollover (Dec -> Jan)
    """
    today = datetime.today()
    # Remove ordinal suffixes
    clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
    # Parse without year
    parsed = datetime.strptime(clean, "%A, %d %B")
    # Assume collection is in the current year
    candidate = parsed.replace(year=today.year)
    if last_date:
        # If this date is earlier than the previous one assume collection is next year
        if candidate.date() < last_date:
            candidate = candidate.replace(year=last_date.year + 1)
        else:
            candidate = candidate.replace(year=last_date.year)
    else:
        # First date: if it's already in the past, assume next year
        if candidate.date() < today.date():
            candidate = candidate.replace(year=today.year + 1)
    return candidate.date()


class Source:
    def __init__(self, uid: str | int):
        self._uid: str = str(uid)

    def fetch(self) -> list[Collection]:

        s = requests.Session()
        r = s.get(f"{API_URL}/{self._uid}")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        last_date = None

        # "Next Collection" section
        next_section = soup.select_one(".collection-next")
        if next_section:
            date_text = (
                next_section.find("h2")
                .get_text(strip=True)
                .replace("Your next collection:", "")
                .strip()
            )
            parsed_date = parse_date_with_rollover(date_text, last_date)
            last_date = parsed_date
            next_bins = [
                item.get_text(strip=True)
                for item in next_section.select(".containers .field__item")
            ]
            for bin in next_bins:
                entries.append(
                    Collection(date=parsed_date, t=bin, icon=ICON_MAP.get(bin))
                )

        # "Other Collections" section
        for li in soup.find("h2", string="Other collections").find_next_siblings("li"):
            containers = li.select(".containers .field__item")
            if not containers:
                continue
            date_text = li.contents[0].strip()
            parsed_date = parse_date_with_rollover(date_text, last_date)
            last_date = parsed_date
            other_bins = [item.get_text(strip=True) for item in containers]
            for bin in other_bins:
                entries.append(
                    Collection(date=parsed_date, t=bin, icon=ICON_MAP.get(bin))
                )

        return entries
