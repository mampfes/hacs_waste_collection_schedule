import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Glasgow City Council"
DESCRIPTION = "Source for www.glasgow.gov.uk services for Glasgow City Council, UK."
URL = "https://www.glasgow.gov.uk/"
TEST_CASES = {
    "test 1 - house": {"uprn": "906700099060"},
    "test 2 - flat": {"uprn": "906700335412"},
}

API_URL = "https://www.glasgow.gov.uk/forms/refuseandrecyclingcalendar/CollectionsCalendar.aspx?UPRN="
ICON_MAP = {
    "purple bins": "mdi:glass-fragile",
    "brown bins": "mdi:apple",
    "green bins": "mdi:trash-can",
    "blue bins": "mdi:recycle",
    "grey bins": "mdi:apple",
}


class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def _parseBins(self, text):
        soup = BeautifulSoup(text, features="html.parser")
        entries = []

        days = soup.find_all("td", {"class": "CalendarDayStyle"})
        for day in days:
            bins = day.find_all("img")

            if len(bins) < 1:
                continue

            date = datetime.strptime(
                day["title"].replace("today is ", ""), "%A, %d %B %Y"
            ).date()

            for bin in bins:
                binname = bin["title"].split()
                binname = f"{binname[0]} {binname[1]}"
                entries.append(
                    Collection(
                        date=date,
                        t=binname,
                        icon=ICON_MAP.get(binname),
                    )
                )

        return entries

    def fetch(self):
        entries = []

        session = requests.Session()

        # get current month
        r = session.get(f"{API_URL}{self._uprn}")
        entries = entries + self._parseBins(r.text)

        # get next month otherwise at end of month you will have no future collection dates
        soup = BeautifulSoup(r.text, features="html.parser")
        nextlink = soup.find("a", title="Go to the next month")
        if len(nextlink) > 0:
            match = re.search(r"__doPostBack\('(.*?)','(.*?)'", nextlink["href"])
            data = {
                "__EVENTTARGET": match.group(1),
                "__EVENTARGUMENT": match.group(2),
                "__EVENTVALIDATION": soup.find("input", id="__EVENTVALIDATION")[
                    "value"
                ],
                "__VIEWSTATE": soup.find("input", id="__VIEWSTATE")["value"],
            }
            r = session.post(f"{API_URL}{self._uprn}", data=data)

            entries = entries + self._parseBins(r.text)

        return entries
