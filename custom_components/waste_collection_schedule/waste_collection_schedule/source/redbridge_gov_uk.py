import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Redbridge Council"
DESCRIPTION = "Source for redbridge.gov.uk services for Redbridge Council, UK."
URL = "https://redbridge.gov.uk"
TEST_CASES = {
    "council office recycling only": {"uprn": 10034922090},
    "refuse and recycling only": {"uprn": 10013585215},
    "a church vicarage, garden, recycling, refuse": {"uprn": 10034912354},
}
ICON_MAP = {
    "REFUSE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        r = requests.get(
            "https://my.redbridge.gov.uk/RecycleRefuse", params={"uprn": self._uprn}
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        services = soup.findAll("div", {"class": re.compile(".*CollectionDay")})

        entries = []

        for service in services:
            waste_type = service.find("h3").text

            month_raw = service.find(
                "div", {"class": re.compile(".*-collection-month")}
            )
            day_raw = service.find(
                "div", {"class": re.compile(".*-collection-day-numeric")}
            )

            if not month_raw or not day_raw:
                # no collection date found for this service
                continue

            # sanitize and extract day, month and optional year (e.g., 'January 2026')
            day_match = re.search(r"(\d{1,2})", day_raw.text.strip())
            month_match = re.search(
                r"([A-Za-z]+)(?:\s+(\d{4}))?", month_raw.text.strip()
            )

            if not day_match or not month_match:
                # not a valid date format
                raise ValueError(
                    f"Can't parse day/month from: day={day_raw.text!r}, month={month_raw.text!r}"
                )

            day = day_match.group(1)
            month = month_match.group(1)
            # sometimes the year is included in the month string
            year_from_month = month_match.group(2)

            if year_from_month:
                year = int(year_from_month)
            else:
                # if guessing the year, assume next year if month has already passed this year
                year = (
                    datetime.now().year + 1
                    if datetime.strptime(month, "%B").month < datetime.now().month
                    else datetime.now().year
                )

            date = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")

            entries.append(
                Collection(
                    date=date.date(),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type.split(" ")[0].upper()),
                )
            )

        return entries
