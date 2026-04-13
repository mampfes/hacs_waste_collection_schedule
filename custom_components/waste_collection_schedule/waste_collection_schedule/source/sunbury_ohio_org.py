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

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": r"No args are required, please enter an empty dict: {}",
}


class Source:
    def __init__(self):
        pass

    def fetch(self):

        s = requests.Session()

        # get page with collection dat and holiday dates
        r = s.get("https://lws-c16afd.webflow.io/service-guidelines/village-of-sunbury")
        soup = BeautifulSoup(r.text, "html.parser")

        # extract collection day and generate collection dates
        collection_day = soup.find("div", {"class": "serviceguidelines_highight"}).text
        start_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        collection_dates = list(
            rrule(
                freq=WEEKLY,
                dtstart=start_date,
                byweekday=DAYS[collection_day],
                count=52,
            )
        )

        # extract holiday dates
        holiday_cells = soup.find_all("div", {"class": "holiday_cell"})[
            3:
        ]  # removes header row
        filtered_list = [
            x for i, x in enumerate(holiday_cells) if i % 3 != 0
        ]  # removes holiday names
        holidays = []
        for item in filtered_list:
            parts = re.split(
                r" - | – ", item.text
            )  # deals with inconsistent hyphenation
            holidays.append(datetime.strptime(parts[1], "%m/%d/%y"))

        # adjust collection dates impacted by holidays
        adjusted_dates = []
        for day in collection_dates:
            week_start = day - timedelta(
                days=day.weekday()
            )  # assume Monday is the start of the week
            # Check if any holiday falls earlier in the same week
            shift_needed = any(week_start <= holiday < day for holiday in holidays)
            if shift_needed:
                adjusted_dates.append((day + timedelta(days=1)).date())
            else:
                adjusted_dates.append(day.date())

        entries = []
        for item in adjusted_dates:
            entries.append(
                Collection(
                    date=item,
                    t="Waste",
                    icon=ICON_MAP.get("Waste"),
                )
            )

        return entries
