import re
from datetime import date, datetime, timedelta

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
    "Test_004": {"uprn": 90092621},
}
ICON_MAP = {"RECYCLING": "mdi:recycle", "GARDEN": "mdi:leaf", "REFUSE": "mdi:trash-can"}
REGEX = {
    "DATES": r"(\d+ \w{3})",
    "DAYS": r"every: (Monday|Tuesday|Wednesday|Thursday|Friday)",
}
DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def check_date(self, d: str, t: datetime, y: int):
        """
        Get date, append year, and increment year if date is >1 month in the past.

        This tries to deal year-end dates when the YEAR is missing
        """
        d += " " + str(y)
        try:
            date = datetime.strptime(d, "%d %b %Y")
        except ValueError:
            date = datetime.strptime(d, "%A %d %b %Y")
        if (date - t) < timedelta(days=-31):
            date = date.replace(year=date.year + 1)
        return date.date()

    def append_entries(self, d: datetime, w: str, e: list) -> list:
        e.append(
            Collection(
                date=d,
                t=w,
                icon=ICON_MAP.get(w.upper()),
            )
        )
        return e

    def get_xmas_map(self, footer_panel) -> dict[date, date]:
        if not (
            footer_panel
            and footer_panel.find("table")
            and footer_panel.find("table").find("tr")
        ):
            return {}
        xmas_map: dict = {}
        today = datetime.now()
        yr = int(today.year)
        for tr in footer_panel.find("table").findAll("tr")[1:]:
            try:
                moved, moved_to = tr.findAll("td")
                moved = self.check_date(moved.text, today, yr)
                moved_to = self.check_date(moved_to.text, today, yr)
                xmas_map[moved] = moved_to
            except Exception as e:
                print(e)
                continue
        return xmas_map

    def fetch(self):
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        yr = int(today.year)

        s = requests.Session()
        r = s.get(
            f"https://maps.dudley.gov.uk/?action=SetAddress&UniqueId={self._uprn}"
        )
        soup = BeautifulSoup(r.text, "html.parser")

        panel = soup.find("div", {"aria-label": "Refuse and Recycling Collection"})
        panel_data = panel.find("div", {"class": "atPanelData"})
        waste_data = panel_data.text.split("Next")[
            1:
        ]  # remove first element it just contains general info

        # get table of holiday moved dates (only around xmas)
        footer_panel = panel.find("div", {"class": "atPanelFooter"})
        xmas_map = self.get_xmas_map(footer_panel)

        entries = []
        # Deal with Recycling and Garden collections
        for item in waste_data:
            text = item.replace("\r\n", "").strip()
            if "recycling" in text:
                dates = re.findall(REGEX["DATES"], text)
                for dt in dates:
                    dt = self.check_date(dt, today, yr)
                    dt = xmas_map.get(dt, dt)
                    self.append_entries(dt, "Recycling", entries)
            elif "garden" in text:
                dates = re.findall(REGEX["DATES"], text)
                for dt in dates:
                    dt = self.check_date(dt, today, yr)
                    dt = xmas_map.get(dt, dt)
                    self.append_entries(dt, "Garden", entries)

        # Refuse collections only have a DAY not a date, so work out dates for the next few collections
        refuse_day = re.findall(REGEX["DAYS"], panel_data.text)[0]
        refuse_date = today + timedelta((int(DAYS[refuse_day]) - today.weekday()) % 7)
        for i in range(0, 4):
            temp_date = (refuse_date + timedelta(days=7 * i)).date()
            temp_date = xmas_map.get(temp_date, temp_date)
            self.append_entries(temp_date, "Refuse", entries)

        return entries
