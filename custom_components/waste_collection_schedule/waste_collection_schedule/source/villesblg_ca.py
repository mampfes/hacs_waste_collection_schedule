from datetime import date, timedelta
from typing import Collection

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection

TITLE = "Ville de Saint-Basile-le-Grand"
DESCRIPTION = "Source for villesblg.ca waste collection calendar"
URL = "https://www.villesblg.ca"
COUNTRY = "ca"
TEST_CASES = {
    "Test 1": {},
}

ICON_MAP = {
    "Ordures": "mdi:trash-can",
    "Recyclage": "mdi:recycle",
    "Résidus verts": "mdi:leaf",
    "Résidus alimentaires": "mdi:food-apple",
        "Encombrants": "mdi:sofa",
        "Dépôt de résidus domestiques dangereux (RDD)": "mdi:spray",
}

FEED_URL = "https://www.villesblg.ca/calendrier-categories/collectes-et-depots/feed/"


def _extract_waste_type(title: str) -> str:
    """Extract waste type from event title."""
    title_lower = title.lower()
    if "ordures" in title_lower:
        return "Ordures"
    if "matières" in title_lower or "récupérables" in title_lower:
        return "Recyclage"
    if "résidus verts" in title_lower:
        return "Résidus verts"
    if "résidus alimentaires" in title_lower:
        return "Résidus alimentaires"
    if "encombrants" in title_lower:
        return "Encombrants"
    if "rebuts" in title_lower:
        return "Dépôt de rebuts"
    return title.strip()


class Source:
    def __init__(self):
        pass

    def fetch(self) -> list[Collection]:
        r = requests.get(FEED_URL)
        r.raise_for_status()

        # Use lxml parser for better XML handling
        soup = BeautifulSoup(r.text, "lxml-xml")
        entries = []

        # Find all item elements in the RSS feed
        items = soup.find_all("item")

        for item in items:
            # Extract waste type from title
            title_tag = item.find("title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            # Extract date from startDay tag (actual collection date)
            start_day = item.find("startDay")
            if not start_day:
                continue
            date_str = start_day.get_text(strip=True)
            if not date_str or date_str == "Aucune":
                continue

            # Parse date in MM/DD/YYYY format
            try:
                month, day, year = date_str.split("/")
                collection_date = date(int(year), int(month), int(day))
            except (ValueError, AttributeError):
                continue

            # Skip dates older than today (allow today and future)
            if collection_date < date.today():
                continue

            waste_type = _extract_waste_type(title)
            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        if not entries:
            raise ValueError(
                "No collection data found. The RSS feed may have changed structure."
            )

        return entries
