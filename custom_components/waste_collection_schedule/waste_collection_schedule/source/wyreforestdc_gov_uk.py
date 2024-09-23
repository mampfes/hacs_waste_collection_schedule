import logging
import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wyre Forest District Council"
DESCRIPTION = "Source for wyreforestdc.gov.uk, Wyre Forest District Council, UK"
URL = "https://www.wyreforestdc.gov.uk"

TEST_CASES = {
    "2 Kinver Avenue, Kidderminster": {
        "street": "hilltop avenue",
        "town": "BEWDLEY",
        "garden_cutomer": "308072",
    },
}

API_URLS = {
    "waste": "https://forms.wyreforestdc.gov.uk/querybin.asp",
    "garden_waste": "https://forms.wyreforestdc.gov.uk/GardenWasteChecker/Home/Details",
}

ICON_MAP = {
    "rubbish (black bin)": "mdi:trash-can",
    "recycling (green bin)": "mdi:recycle",
    "garden waste (brown bin)": "mdi:leaf",
}

DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

# Next Rubbish Collection
REGEX_GET_BIN_TYPE = re.compile(r"Next (.*?) Collection")
# collection is on a WEDNESDAY and will be collected on the same week as your rubbish bin collection
REGEX_GET_GARDEN_DAY = re.compile(
    r"collection is on a\s*(.*?)\s*and will be collected on the same week as"
)
REGEX_GET_GARDEN_SAME_WEEK_AS = re.compile(
    r"collected on the same week as your\s*(.*?)\s*(bin)?\s*collection"
)

_LOGGER = logging.getLogger(__name__)


def get_date_by_weekday(weekday: str) -> date:
    this_week = re.match("This (.*?)$", weekday, re.IGNORECASE)
    next_week = re.match("Next (.*?)$", weekday, re.IGNORECASE)
    if this_week:
        weekday_idx = DAYS.index(this_week.group(1).upper())
        offset = 0
    elif next_week:
        weekday_idx = DAYS.index(next_week.group(1).upper())
        offset = 7
    else:
        raise ValueError(f"Invalid weekday: {weekday}")

    d = date.today() + timedelta(days=offset)
    while d.weekday() != weekday_idx:
        d += timedelta(days=1)
    return d


def predict_next_collections(first_date: date, day_interval: int = 14):
    return [first_date + timedelta(days=i * day_interval) for i in range(5)]


class Source:
    def __init__(self, street: str, town: str, garden_cutomer: str | int | None = None):
        self._street = street.upper().strip()
        self._town = town.upper().strip()
        self._garden_cutomer = str(garden_cutomer).strip() if garden_cutomer else None

    def get_garden_waste(self, type_to_day: dict[str, str]) -> list[Collection]:
        data = {
            "CUST_No": self._garden_cutomer,
        }
        r = requests.post(API_URLS["garden_waste"], data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        day = REGEX_GET_GARDEN_DAY.search(soup.text)
        same_week_as = REGEX_GET_GARDEN_SAME_WEEK_AS.search(soup.text)
        if not day or not same_week_as:
            raise ValueError(
                f"Could not find garden waste collection days: {day} {same_week_as}"
            )

        relevant_coll_date = get_date_by_weekday(
            type_to_day[same_week_as.group(1).lower()]
        )
        monday_of_garden_week = relevant_coll_date - timedelta(
            days=relevant_coll_date.weekday()
        )

        garden_day = monday_of_garden_week + timedelta(DAYS.index(day.group(1).upper()))
        entries = []
        for coll_date in predict_next_collections(garden_day):
            entries.append(
                Collection(
                    date=coll_date,
                    icon=ICON_MAP.get("garden waste"),
                    t="Garden waste",
                )
            )
        return entries

    def fetch(self) -> list[Collection]:
        entries: list[Collection] = []
        params = {
            "txtStreetName": self._street,
            "select": "yes",
            "town": self._town,
        }
        r = requests.post(API_URLS["waste"], params=params)
        r.raise_for_status()
        type_to_day: dict[str, str] = {}

        soup = BeautifulSoup(r.text, "html.parser")
        coll_day_header_p = soup.find("p", text="Collection Day")

        if not coll_day_header_p:
            raise ValueError("Could not find collection day header")
        coll_day_table = coll_day_header_p.find_parent("table")
        if not coll_day_table:
            raise ValueError("Could not find collection day table")
        coll_day_rows = coll_day_table.find_all("tr")
        if not len(coll_day_rows) == 2:
            raise ValueError("Could not find collection day rows")

        headings = [td.text.strip() for td in coll_day_rows[0].find_all("td")]
        values = [td.text.strip() for td in coll_day_rows[1].find_all("td")]

        for heading, value in list(zip(headings, values)):
            if REGEX_GET_BIN_TYPE.match(heading):
                bin_type_match = REGEX_GET_BIN_TYPE.match(heading)
                if not bin_type_match:
                    raise ValueError(f"Could not find bin type in heading: {heading}")
                bin_type = bin_type_match.group(1)

                type_to_day[bin_type.lower()] = value

                for coll_date in predict_next_collections(get_date_by_weekday(value)):
                    entries.append(
                        Collection(
                            date=coll_date,
                            icon=ICON_MAP.get(bin_type),
                            t=bin_type,
                        )
                    )

        if self._garden_cutomer:
            entries += self.get_garden_waste(type_to_day)

        return entries
