import json
from datetime import datetime

import re

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

from bs4 import BeautifulSoup

TITLE = "Glasgow City Council"
DESCRIPTION = (
    "Source for www.glasgow.gov.uk services for Glasgow City Council, UK."
)
URL = "https://www.glasgow.gov.uk/"
TEST_CASES = {
    "test 1 - house": {"uprn": "906700099060"},
    "test 2 - flat": {"uprn": "906700335412"}
}

API_URL = "https://www.glasgow.gov.uk/forms/refuseandrecyclingcalendar/CollectionsCalendar.aspx?UPRN="
ICON_MAP = {
    "purple bins": "mdi:glass-fragile",
    "brown bins": "mdi:apple",
    "green bins": "mdi:trash-can",
    "blue bins": "mdi:recycle",
    "GREY bins": "mdi:apple",
}

from pprint import pprint

class Source:
    def __init__(self, uprn: str):
        self._uprn = uprn

    def __parseBins(self, soup):
            entries = []
            
            days = soup.find_all("td", {"class": "CalendarDayStyle"})
            for day in days:
                bins = day.find_all("img")

                if len(bins) < 1:
                    continue

                date = datetime.strptime(day["title"].replace("today is ",""), "%A, %d %B %Y").date()

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
        if self._uprn is None:
            raise Exception("No uprn supplied")        
        entries = []

        session = requests.Session()

        # get current month
        r = session.get(f"{API_URL}{self._uprn}")
        soup = BeautifulSoup(r.text, features="html.parser")
        entries = entries + self.__parseBins(soup)

        # get next month otherwise at end of month you will have no future collection dates
        nextlink = soup.find("a", title="Go to the next month")
        if len(nextlink) > 0:
            match = re.search(r"__doPostBack\('(.*?)','(.*?)'", nextlink["href"])
            eventtarget = match.group(1)
            eventargument = match.group(2)
            eventvalidation = soup.find("input", id="__EVENTVALIDATION")["value"]
            viewstate = soup.find("input", id="__VIEWSTATE")["value"]
            data = {
                "__EVENTTARGET": eventtarget,
                "__EVENTARGUMENT": eventargument,
                "__EVENTVALIDATION": eventvalidation,
                "__VIEWSTATE": viewstate
            }        
            r =session.post(f"{API_URL}{self._uprn}", data=data)

            soup = BeautifulSoup(r.text, features="html.parser")
            entries = entries + self.__parseBins(soup)

        return entries
