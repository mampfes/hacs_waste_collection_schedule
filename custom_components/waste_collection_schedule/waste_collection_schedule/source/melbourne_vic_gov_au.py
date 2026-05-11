from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Melbourne"
DESCRIPTION = "Source for City of Melbourne waste collection schedules."
URL = "https://www.melbourne.vic.gov.au"
TEST_CASES = {
    "Monday zone (North Melbourne area)": {
        "lat": -37.78888528182715,
        "lon": 144.94807224053946,
    },
    "Tuesday zone (CBD south)": {
        "lat": -37.82597212079299,
        "lon": 144.946122910589,
    },
    "Wednesday zone (Carlton area)": {
        "lat": -37.797770217788965,
        "lon": 144.96108202950762,
    },
    "Thursday zone (West Melbourne area)": {
        "lat": -37.80199461843715,
        "lon": 144.92363364191561,
    },
    "Friday zone (East Melbourne area)": {
        "lat": -37.81350068415623,
        "lon": 144.98033118663488,
    },
}

ICON_MAP = {
    "General waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

API_URL = "https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/garbage-collection-zones/records"


class Source:
    def __init__(self, lat: float, lon: float):
        self._lat = float(lat)
        self._lon = float(lon)

    def fetch(self) -> list[Collection]:
        params = {
            "limit": 1,
            "select": "rub_name,rec_name,rub_day,rec_day,rub_weeks,rec_weeks,rub_start,rec_start",
            "where": f"intersects(geo_shape, geom'POINT({self._lon} {self._lat})')",
        }
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            raise SourceArgumentNotFound(
                "lat/lon",
                f"{self._lat}, {self._lon}",
            )

        zone = results[0]
        entries: list[Collection] = []

        for day_key, name_key, weeks_key, start_key in [
            ("rub_day", "rub_name", "rub_weeks", "rub_start"),
            ("rec_day", "rec_name", "rec_weeks", "rec_start"),
        ]:
            day_name = zone.get(day_key, "").lower()
            waste_name = zone.get(name_key, "")
            weeks = int(zone.get(weeks_key, 1))
            start_str = zone.get(start_key, "")

            weekday_num = WEEKDAY_MAP.get(day_name)
            if weekday_num is None:
                continue

            # Determine the start date (used for fortnightly parity)
            try:
                start_date = datetime.strptime(start_str, "%Y/%m/%d").date()
            except (ValueError, TypeError):
                start_date = date.today()

            today = date.today()

            # Find the first occurrence on or after the start_date that lands
            # on the correct weekday
            days_to_first = (weekday_num - start_date.weekday()) % 7
            first_occurrence = start_date + timedelta(days=days_to_first)

            # Advance to the next occurrence on or after today
            if first_occurrence < today:
                delta = (today - first_occurrence).days
                weeks_elapsed = delta // (7 * weeks)
                next_date = first_occurrence + timedelta(weeks=weeks_elapsed * weeks)
                if next_date < today:
                    next_date += timedelta(weeks=weeks)
            else:
                next_date = first_occurrence

            icon = ICON_MAP.get(waste_name)
            # Generate approximately one year of upcoming dates
            end_date = today + timedelta(days=365)
            current = next_date
            while current <= end_date:
                entries.append(
                    Collection(
                        date=current,
                        t=waste_name,
                        icon=icon,
                    )
                )
                current += timedelta(weeks=weeks)

        return entries
