import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Village of Sunbury, Ohio"
DESCRIPTION = "Source for Village of Sunbury, Ohio"
URL = "https://www.sunburyohio.org"
TEST_CASES: dict[str, dict] = {"TEST": {}}
ICON_MAP = {
    "Waste": "mdi:trash-can",
}
COUNTRY = "us"
DAYS = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}

API_URL = "https://lws-c16afd.webflow.io/service-guidelines/village-of-sunbury"

DATE_RE = re.compile(r"\d{1,2}/\d{1,2}/\d{2}")


class Source:
    def __init__(self):
        pass

    def fetch(self):
        s = requests.Session()

        r = s.get(API_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # extract collection day and generate weekly dates
        collection_day_el = soup.find("div", {"class": "serviceguidelines_highight"})
        collection_day = DAYS[collection_day_el.text.strip().upper()]
        start_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        collection_dates = list(
            rrule(
                freq=WEEKLY,
                dtstart=start_date,
                byweekday=collection_day,
                count=52,
            )
        )

        # extract holiday dates from all holiday cells by matching date patterns
        holidays = []
        for cell in soup.find_all("div", {"class": "holiday_cell"}):
            match = DATE_RE.search(cell.text)
            if match:
                try:
                    holidays.append(datetime.strptime(match.group(), "%m/%d/%y"))
                except ValueError:
                    continue

        # adjust collection dates: shift +1 day if a holiday falls earlier in the same week
        entries = []
        for day in collection_dates:
            week_start = day - timedelta(days=day.weekday())
            shift_needed = any(week_start <= holiday < day for holiday in holidays)
            date = (day + timedelta(days=1)).date() if shift_needed else day.date()
            entries.append(
                Collection(
                    date=date,
                    t="Waste",
                    icon=ICON_MAP.get("Waste"),
                )
            )

        return entries
