from datetime import date, datetime, timedelta
from typing import Any, final

import requests
from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

# Demonstrates: a source with two independent fetches (the city's observed
# holiday feed + the address record) combined in a custom retrieve(), then a
# recurrence projection plus Philadelphia's same-week cascading holiday shift in
# the preprocessor. The holiday calendar is the city's own published feed, not
# the holidays library, so observed dates match the provider exactly.

HOLIDAYS_URL = "https://api.phila.gov/phila/trashday/v1"
ADDRESS_URL = "https://api.phila.gov/ais/v1/addresses/{address}"
HEADERS = {"user-agent": "Mozilla/5.0"}

DAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def _shift_for_holidays(holidays: list[date], dt: date) -> date:
    """Shift a collection forward for holidays earlier in its Mon-Sun week.

    Each weekday holiday on or before the collection day pushes it one day; if
    the shifted day is itself a holiday, shift again (per phila.gov's rules).
    """
    week_start = dt - timedelta(days=dt.weekday())
    week_end = week_start + timedelta(days=6)
    week_holidays = sorted(h for h in holidays if week_start <= h <= week_end)
    shift = sum(1 for h in week_holidays if h <= dt)
    adjusted = dt + timedelta(days=shift)
    if adjusted in holidays and adjusted != dt:
        return _shift_for_holidays(holidays, adjusted)
    return adjusted


@final
class Source(BaseSource):
    TITLE = "City of Philadelphia, PA"
    DESCRIPTION = "City of Philadelphia, PA, USA"
    URL = "https://www.phila.gov/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES = [GENERAL_WASTE, RECYCLABLES]

    TEST_CASES = {
        "Test_001": {"address": "1830 Fitzwater Street"},
        "Test_002": {"address": "9868 Cowden St"},
        "Test_003": {"address": "582 Paoli Ave"},
        "Test_004": {"address": "2714 S Marvine St"},
    }

    PARAMS = [text_field("address", label="Address")]

    HOWTO = {
        "en": "Use your address as shown on the phila.gov trash/recycling "
        "collection-day search results.",
    }

    def __init__(self, address: str):
        super().__init__(address=address)
        self._address = address.upper()

    def retrieve(self, source):
        # Two independent fetches: the city's observed holidays and the property.
        # Uses plain requests, not the curl_cffi session: api.phila.gov serves a
        # 202 bot-challenge to the impersonated-Chrome client.
        holidays_resp = requests.get(HOLIDAYS_URL, headers=HEADERS, timeout=30)
        address_resp = requests.get(
            ADDRESS_URL.format(address=self._address), headers=HEADERS, timeout=30
        )
        return {"holidays": holidays_resp.json(), "address": address_resp.json()}

    def parse(self, raw, source):
        return raw

    def preprocessor(self, records, source=None):
        data: dict[str, Any] = records

        # Weekday holidays only (weekend ones never affect collections).
        holidays = [
            datetime.strptime(item["start_date"], "%Y-%m-%d").date()
            for item in data["holidays"]["holidays"]
        ]
        holidays = [h for h in holidays if h.weekday() < 5]

        props = data["address"]["features"][0]["properties"]
        waste_days: list[int] = []
        recycle_days: list[int] = []
        for key, value in props.items():
            if not isinstance(value, str) or value.upper() not in DAYS:
                continue
            day = DAYS[value.upper()]
            if "rubbish" in key.lower():
                waste_days.append(day)
            if key.lower() == "rubbish_recycle_day":
                recycle_days.append(day)

        year = date.today().year
        start, end = date(year, 1, 1), date(year, 12, 31)
        weeks = 53

        def dates_for(weekdays: list[int]) -> set[date]:
            out: set[date] = set()
            for wd in weekdays:
                first = recurrence.next_weekday(wd, on_or_after=start)
                for d in recurrence.recurring(first, recurrence.WEEKLY, weeks):
                    if d <= end:
                        out.add(_shift_for_holidays(holidays, d))
            return out

        for d in dates_for(waste_days):
            yield {"date": d, "waste_type": GENERAL_WASTE}
        for d in dates_for(recycle_days):
            yield {"date": d, "waste_type": RECYCLABLES}

    def classify(self, record) -> Collection:
        return Collection(date=record["date"], waste_type=record["waste_type"])
