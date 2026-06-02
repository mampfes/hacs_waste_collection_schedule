from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Ville de Saint-Basile-le-Grand"
DESCRIPTION = "Source for villesblg.ca waste collection calendar"
URL = "https://www.villesblg.ca"
COUNTRY = "ca"
TEST_CASES = {
    "Test 1": {},
}

ICON_MAP = {
    "Ordures": Icons.GENERAL_WASTE,
    "Recyclage": Icons.RECYCLING,
    "Résidus verts": Icons.ORGANIC,
    "Résidus alimentaires": Icons.BIO_KITCHEN,
    "Encombrants": Icons.BULKY,
}

FEED_URL = "https://www.villesblg.ca/calendrier-categories/collectes-et-depots/feed/"


def _extract_waste_type(title: str) -> str:
    """Extract waste type from event title."""
    title_lower = title.lower()
    if "ordures" in title_lower:
        return "Ordures"
    if "matières récupérables" in title_lower:
        return "Recyclage"
    if "résidus verts" in title_lower:
        return "Résidus verts"
    if "résidus alimentaires" in title_lower:
        return "Résidus alimentaires"
    if "encombrants" in title_lower:
        return "Encombrants"
    return title.strip()


class Source:
    def __init__(self):
        pass

    def fetch(self) -> list[Collection]:
        r = requests.get(FEED_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml-xml")
        entries = []

        for item in soup.find_all("item"):
            title_tag = item.find("title")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)

            if "rebuts" in title.lower() or "dangereux" in title.lower():
                continue

            start_day = item.find("startDay")
            if not start_day:
                continue
            date_str = start_day.get_text(strip=True)
            if not date_str or date_str == "Aucune":
                continue

            try:
                day, month, year = date_str.split("/")
                collection_date = date(int(year), int(month), int(day))
            except (ValueError, AttributeError):
                continue

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
