from datetime import datetime, timedelta
import re
import requests

from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]


TITLE = "Dudley Metropolitan Borough Council"
DESCRIPTION = "Source for Dudley Metropolitan Borough Council, UK."
URL = "https://dudley.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "90090715"},
    "Test_002": {"uprn": 90104555},
    "Test_003": {"uprn": "90164803"},
    "Test_004": {"uprn": 90092621}
}
ICON_MAP = {
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
    "REFUSE": "mdi:trash-can"
}
REGEX = r"(\d+ \w{3})"


class Source:
    def __init__(self, uprn: str|int):
        self._uprn = str(uprn)

    def check_date(self, d: str, t: datetime, y: int ):
        """
        Get date, append year, and increment year if date is >1 month in the past.
        This tries to deal year-end dates when the YEAR is missing
        """
        d += " " + str(y)
        d = datetime.strptime(d, "%d %b %Y")
        if (d - t) < timedelta(days=-31):
            d = d.replace(year = d.year + 1)
        return d.date()

    def append_entries(self, d: datetime, w: str, e: list):
        """
        Refuse is collected on the same dates as alternating Recycling/Garden collections,
        so create two entries for each date Refuse & Recycling, or Refuse & Garden
        """
        e.append(
            Collection(
                date=d,
                t=w,
                icon=ICON_MAP.get(w.upper()),
            )
        )
        e.append(
            Collection(
                date=d,
                t="Refuse",
                icon=ICON_MAP.get("REFUSE"),
            )
        )
        return e

    def fetch(self):

        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        yr = int(today.year)

        s = requests.Session()
        r = s .get(f"https://maps.dudley.gov.uk/?action=SetAddress&UniqueId={self._uprn}")
        soup = BeautifulSoup(r.text, "html.parser")

        panel = soup.find("div",{"aria-label": "Refuse and Recycling Collection"})
        panel_data = panel.find("div", {"class": "atPanelData"})
        panel_data = panel_data.text.split("Next")[1:]  # remove first element it just contains general info

        entries = []
        for item in panel_data:
            text = item.replace("\r\n", "").strip()
            if "recycling" in text:
                dates = re.findall(REGEX, text)
                for dt in dates:
                    dt = self.check_date(dt, today, yr)
                    self.append_entries(dt, "Recycling", entries)
            elif "garden" in text:
                dates = re.findall(REGEX, text)
                for dt in dates:
                    dt = self.check_date(dt, today, yr)
                    self.append_entries(dt, "Garden", entries)

        return entries
