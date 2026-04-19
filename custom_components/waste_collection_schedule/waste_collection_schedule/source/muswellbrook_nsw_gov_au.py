import datetime

import requests
from bs4 import BeautifulSoup

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Muswellbrook Shire Council"
DESCRIPTION = "Source for Muswellbrook Shire Council, NSW, Australia."
URL = "https://www.muswellbrook.nsw.gov.au"
TEST_CASES = {
    "Zone 3A": {"zone": "3a"},
    "Zone 5B": {"zone": "5b"},
    "Zone 1B": {"zone": "1b"},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your collection zone at https://www.muswellbrook.nsw.gov.au/waste-collection/ and enter it as e.g. '3a' or '5b'."
}
PARAM_DESCRIPTIONS = {
    "en": {
        "zone": "Collection zone, e.g. '3a' or '5b'. Find your zone at https://www.muswellbrook.nsw.gov.au/waste-collection/"
    }
}

ICON_MAP = {
    "general waste": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "fogo": "mdi:leaf",
}

COLLECTION_URL = "https://www.muswellbrook.nsw.gov.au/waste-collection/zone-{}/"
LOOKAHEAD_WEEKS = 52


class Source:
    def __init__(self, zone: str):
        self._zone = zone.lower().strip()

    def fetch(self) -> list[Collection]:
        r = requests.get(COLLECTION_URL.format(self._zone))
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        bins = []
        for block in soup.find_all(class_="waste-block"):
            title_el = block.find(class_="waste-block__title")
            often_el = block.find(class_="waste-block__often")
            time_el = block.find(class_="waste-block__time")

            if not title_el or not often_el or not time_el:
                continue

            title = title_el.get_text(strip=True)
            often = often_el.get_text(strip=True).lower()
            dt_str = time_el.get("datetime", "")

            try:
                next_date = datetime.date.fromisoformat(dt_str[:10])
            except (ValueError, IndexError):
                continue

            interval = datetime.timedelta(weeks=1 if "weekly" in often else 2)
            bins.append((title, next_date, interval))

        if not bins:
            raise SourceArgumentNotFound("zone", self._zone)

        entries = []
        end_date = datetime.date.today() + datetime.timedelta(weeks=LOOKAHEAD_WEEKS)

        for title, next_date, interval in bins:
            d = next_date
            while d <= end_date:
                # Christmas Day collections are moved to Boxing Day
                if d.month == 12 and d.day == 25:
                    d += datetime.timedelta(days=1)
                entries.append(
                    Collection(
                        date=d,
                        t=title,
                        icon=self._get_icon(title),
                    )
                )
                d += interval

        return entries

    def _get_icon(self, waste_type: str) -> str | None:
        lower = waste_type.lower()
        for key, icon in ICON_MAP.items():
            if key in lower:
                return icon
        return None
