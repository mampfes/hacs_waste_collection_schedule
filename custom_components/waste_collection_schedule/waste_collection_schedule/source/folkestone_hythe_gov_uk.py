from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Folkestone and Hythe District Councol"
DESCRIPTION = "Source for Folkestone and Hythe District Council, United Kingdom."
URL = "https://www.folkestone-hythe.gov.uk/"
TEST_CASES = {
    "Folkestone_Test": {"uprn": 50032102},
    "Hythe_Test": {"uprn": "50019287"},
}
ICON_MAP = {
    "Recycling (mixed)": Icons.RECYCLING,
    "Paper & Card": Icons.PAPER,
    "Food Waste": Icons.BIO_KITCHEN,
    "General Waste": Icons.GENERAL_WASTE,
    "Garden Waste": Icons.GARDEN,
}
BASE_URL = "https://service.folkestone-hythe.gov.uk/webapp/myarea"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()
        # The council now loads the collections via JavaScript from
        # api_collections.php. Visit the page first to obtain a session cookie.
        page_url = f"{BASE_URL}/index.php?uprn={self._uprn}&tab=collections"
        r = s.get(page_url)
        r.raise_for_status()

        r = s.get(
            f"{BASE_URL}/api_collections.php",
            params={"uprn": self._uprn},
            headers={"Referer": page_url, "X-Requested-With": "fetch"},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select("article.service-card")
        if not cards:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "Folkestone and Hythe returned no collections for this UPRN. "
                "Check it against the council's own address search; if the "
                "UPRN is correct there, the council has probably changed its "
                "API - please open an issue.",
            )

        entries = []
        for card in cards:
            title = card.select_one(".service-title")
            next_time = card.select_one(".service-next time")
            if title is None or next_time is None:
                continue
            waste_type = title.get_text(strip=True)
            dt = next_time.get("datetime")
            if not isinstance(dt, str):
                continue
            # datetime attribute is ISO 8601, e.g. 2026-10-05T00:00:00+01:00
            date = datetime.strptime(dt[:10], "%Y-%m-%d").date()
            entries.append(
                Collection(date=date, t=waste_type, icon=ICON_MAP.get(waste_type))
            )

        return entries
