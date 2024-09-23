from datetime import datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Rhondda Cynon Taf County Borough Council"
DESCRIPTION = "Source for rctcbc.gov.uk services for Rhondda Cynon Taf County Borough Council, Wales, UK"
URL = "rctcbc.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10024274791"},
    "Test_002": {"uprn": "100100718352"},
    "Test_003": {"uprn": 100100733093},
}
ICON_MAP = {
    "BLACK BAGS": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "FOOD WASTE": "mdi:food",
    "GARDEN WASTE": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def extract_collections(self, calendar: Tag | BeautifulSoup) -> list[Collection]:
        calendar_month = calendar.find("div", {"class": "calendar-month"})
        if not calendar_month or not isinstance(calendar_month, Tag):
            return []
        month = calendar_month.text.strip()
        calendar_days = calendar.find_all(
            "div", {"class": "card-body card-body-padding"}
        )

        entries = []
        for day in calendar_days:
            pickups = day.find_all("a")
            if len(pickups) != 0:
                d = day.find("div", {"class": "card-title"})
                if not d or not isinstance(d, Tag):
                    continue
                dt = d.text.strip() + " " + month
                for pickup in pickups:
                    entries.append(
                        Collection(
                            date=datetime.strptime(
                                dt,
                                "%d %B %Y",
                            ).date(),
                            t=pickup.text,
                            icon=ICON_MAP.get(pickup.text.upper()),
                        )
                    )
        return entries

    def extract_from_printable_calendar(
        self, soup: BeautifulSoup
    ) -> list[Collection] | None:
        entries = []
        printable_calendar = soup.find("div", {"class": "printableCalendar"})
        if not printable_calendar or not isinstance(printable_calendar, Tag):
            return None

        calendars = printable_calendar.find_all(
            "div", {"class": "calendar-wrap onlyPrint"}
        )
        if not calendars:
            return None

        for calendar in calendars:
            if not calendar or not isinstance(calendar, Tag):
                continue
            entries += self.extract_collections(calendar)
        return entries or None

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        # website appears to display ~4 months worth of collections, so iterate through those pages
        entries: list[Collection] = []
        for month in range(0, 4):
            r = s.get(
                f"https://www.rctcbc.gov.uk/EN/Resident/RecyclingandWaste/RecyclingandWasteCollectionDays.aspx?uprn={self._uprn}&month={month}"
            )
            soup = BeautifulSoup(r.text, "html.parser")
            printable_calendar_entries = self.extract_from_printable_calendar(soup)
            if printable_calendar_entries:
                return printable_calendar_entries

            # OLD METHOD IF THEY EVER REMOVE THE PRINTABLE CALENDAR AGAIN:
            calendar = soup.find("div", {"class": "monthlyCalendar"}) or soup
            if not isinstance(calendar, Tag):
                continue
            entries += self.extract_collections(calendar)

        return entries
