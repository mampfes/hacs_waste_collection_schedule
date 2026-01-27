from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentRequired,
)
TITLE = "City of San Antonio"
DESCRIPTION = "Source for City of San Antonio, Texas waste collection."
URL = "https://www.sa.gov/Directory/Departments/SWMD/Resources/CollectionSchedule"
HOW_TO_GET_ARGUMENTS_DESCRIPTION = { 
    "en": "The source argument is the street number and street name to the house with waste collection. The address can be tested [here](https://www.sa.gov/Directory/Departments/SWMD/Brush-Bulky/My-Collection-Day).",
}
PARAM_DESCRIPTIONS = {
    "en": {
    "address": "Street number and street name (e.g., 123 Main St)",
    }
}


API_URL = "https://gis.sanantonio.gov/swmd/mycollectionday/Request.aspx?addr={addr}"
COUNTRY = "us"
TEST_CASES = {
    "H-E-B Corporate Office Headquarters": {"address": "646 S Flores St"},
    "Freeman Coliseum": { "address": "3201 E Houston St"},
    "Witte Museum": { "address": "3801 Broadway"},
}



ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycle": "mdi:recycle",
    "Organics": "mdi:leaf",
    "Brush": "mdi:tree",
    "Bulky": "mdi:sofa",
}

DAY_OF_WEEK = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def _get_thanksgiving(year: int) -> date:
    nov_first = date(year, 11, 1)
    days_until_thursday = (3 - nov_first.weekday()) % 7
    first_thursday = nov_first + timedelta(days=days_until_thursday)
    return first_thursday + timedelta(weeks=3)


def _get_mlk_day(year: int) -> date:
    jan_first = date(year, 1, 1)
    days_until_monday = (0 - jan_first.weekday()) % 7
    first_monday = jan_first + timedelta(days=days_until_monday)
    return first_monday + timedelta(weeks=2)


def _get_shifting_holidays(year: int) -> list[date]:
    return [
        _get_thanksgiving(year),
        date(year, 12, 25),
        date(year, 1, 1),
        _get_mlk_day(year),
    ]


def _get_week_bounds(d: date) -> tuple[date, date]:
    days_since_sunday = (d.weekday() + 1) % 7
    week_start = d - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def _adjust_for_holidays(collection_date: date) -> date:
    collection_dow = collection_date.weekday()

    if collection_dow > 4:
        return collection_date

    for year in range(collection_date.year - 1, collection_date.year + 2):
        for holiday in _get_shifting_holidays(year):
            week_start, week_end = _get_week_bounds(holiday)

            if week_start <= collection_date <= week_end:
                if collection_dow >= holiday.weekday():
                    return collection_date + timedelta(days=1)

    return collection_date


def _get_next_day_of_week(day_name: str, *, weeks: int = 4) -> list[date]:
    day_name = day_name.upper().strip()
    if day_name not in DAY_OF_WEEK:
        return []

    target_weekday = DAY_OF_WEEK[day_name]
    today = date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead < 0:
        days_ahead += 7

    first_date = today + timedelta(days=days_ahead)
    dates = [first_date + timedelta(weeks=i) for i in range(weeks)]

    return [_adjust_for_holidays(d) for d in dates]


def _parse_week_of_date(date_str: str) -> date | None:
    if not date_str or not date_str.startswith("Week of "):
        return None
    date_part = date_str.replace("Week of ", "").strip()
    return datetime.strptime(date_part, "%m/%d/%Y").date()


class Source:
    def __init__(self, address: str):
        if address is None or address.strip() == "":
            raise SourceArgumentRequired("address", "Address is required")
        self._address: str = address

    def fetch(self) -> list[Collection]:
        r = requests.get(
API_URL.format(addr=requests.utils.quote(self._address)),
timeout=30,
)
        r.raise_for_status()
        data = r.json()
        if data == []:
            raise ValueError("Address not found")

        entries: list[Collection] = []

        if not data:
            return entries

        attributes = data[0].get("attributes", {})
        no_service = True
        for waste_type in ("Garbage", "Recycle", "Organics"):
            day_name = attributes.get(waste_type)
            no_svc = day_name == "NO SERVICE"
            no_service &= no_svc
            if not day_name or no_svc:
                continue

            if waste_type == "Organics" and not attributes.get("isQualifyOrganics"):
                continue

            for collection_date in _get_next_day_of_week(day_name):
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        for waste_type in ("Brush", "Bulky"):
            date_str = attributes.get(waste_type)
            collection_date = _parse_week_of_date(date_str)
            if collection_date:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )
        if no_service and not entries:
            raise ValueError(f"No waste collection service found for {self._address}")
        return entries