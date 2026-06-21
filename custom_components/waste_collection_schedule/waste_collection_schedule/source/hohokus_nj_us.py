import re
from datetime import date, timedelta

from bs4 import BeautifulSoup
from waste_collection_schedule import recurrence, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GARDEN_WASTE, GENERAL_WASTE

# Demonstrates: seasonal/windowed recurrence (Schedule.not_before/until).
#
# The Borough of Ho-Ho-Kus publishes a *rule*, not explicit dates: a property's
# district has two solid-waste weekdays in season (1 April - 31 October) and a
# single weekday out of season (1 November - 31 March). Yard waste is collected
# on the in-season solid-waste days and suspended out of season. So the schedule
# is projected from the rule, exercising two seasonal shapes:
#   * garbage: cadence changes by season (two days in summer, one in winter,
#     the winter window crossing the year boundary),
#   * yard waste: a clean seasonal suspension (none in winter).
# The district weekdays and the season window are read live from the page, so
# nothing is hardcoded.

API_URL = (
    "https://www.hhkborough.com/recycling-solid-waste/pages/"
    "trash-recycling-special-events-schedule"
)

# "If your regular pick-up is Monday & Thursday, (District 1) ... only on Thursday"
_DISTRICT_RE = re.compile(
    r"pick-?up is (\w+)\s*(?:&|and)\s*(\w+),?\s*\(District\s*(\d)\).*?only on (\w+)",
    re.IGNORECASE | re.DOTALL,
)
# "April 1 - October 31" — the in-season window (first such span on the page).
_SEASON_RE = re.compile(r"(\w+)\s+(\d{1,2})\s*-\s*(\w+)\s+(\d{1,2})")

# How far ahead to project (a little over a year, so the upcoming season is
# always covered without generating an unbounded number of dates).
_HORIZON_DAYS = 400

GENERAL = "general waste"
YARD = "yard waste"


def _window(key, weekday, start, end, today, horizon):
    """One windowed Schedule for ``weekday`` within ``[start, end]`` (clipped).

    Yields nothing when the window is entirely in the past or beyond the
    horizon, so past seasons drop out and only upcoming collections remain.
    """
    until = min(end, horizon)
    not_before = max(start, today)
    if not_before > until:
        return
    phase = recurrence.next_weekday(weekday, on_or_after=start)
    yield Schedule(key, phase, recurrence.WEEKLY, not_before=not_before, until=until)


def _describe(record, source):
    summer_days = record["summer_days"]
    winter_day = record["winter_day"]
    start_month, start_day, end_month, end_day = record["season"]

    today = date.today()
    horizon = today + timedelta(days=_HORIZON_DAYS)

    # Cover the in-progress and upcoming seasons (past windows yield nothing).
    for year in (today.year - 1, today.year, today.year + 1):
        in_start = date(year, start_month, start_day)
        in_end = date(year, end_month, end_day)
        out_start = in_end + timedelta(days=1)
        out_end = date(year + 1, start_month, start_day) - timedelta(days=1)

        for weekday in summer_days:
            # In season: garbage AND yard waste on each solid-waste day.
            yield from _window(GENERAL, weekday, in_start, in_end, today, horizon)
            yield from _window(YARD, weekday, in_start, in_end, today, horizon)
        # Out of season: garbage once a week; no yard waste.
        yield from _window(GENERAL, winter_day, out_start, out_end, today, horizon)


class Source(BaseSource):
    TITLE = "Borough of Ho-Ho-Kus"
    DESCRIPTION = "Source for the Borough of Ho-Ho-Kus, New Jersey, USA."
    URL = "https://www.hhkborough.com"
    COUNTRY = "us"
    CODEOWNERS = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "District 1 (Mon/Thu)": {"district": "District 1"},
        "District 2 (Tue/Fri)": {"district": "District 2"},
    }

    PARAMS = [dropdown("district", ["District 1", "District 2"], label="District")]

    HOWTO = {
        "en": (
            "Select your collection district (1 or 2). The borough collects yard "
            "waste on your two solid-waste days from 1 April to 31 October, and "
            "garbage once a week the rest of the year; the days and season are "
            "read from the borough schedule page."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(url=API_URL)

    preprocessor = RecurrenceExpander(_describe)

    transformer = ICSTransformer(
        type_value_map={GENERAL: GENERAL_WASTE, YARD: GARDEN_WASTE},
    )

    def __init__(self, district: str):
        super().__init__(district=district)
        match = re.search(r"\d", district)
        if match is None:
            raise SourceArgumentNotFound("district", district)
        self._district = match.group(0)

    def parse(self, response, source):
        text = re.sub(
            r"\s+", " ", BeautifulSoup(response.text, "html.parser").get_text(" ")
        )

        districts: dict[str, tuple] = {}
        for day1, day2, num, winter in _DISTRICT_RE.findall(text):
            weekdays = (
                recurrence.weekday(day1),
                recurrence.weekday(day2),
                recurrence.weekday(winter),
            )
            if all(wd is not None for wd in weekdays):
                districts[num] = weekdays

        if self._district not in districts:
            raise SourceArgumentNotFound(
                "district", self._district, "could not read this district's days"
            )

        season_match = _SEASON_RE.search(text)
        start_month = recurrence.month(season_match.group(1)) if season_match else None
        end_month = recurrence.month(season_match.group(3)) if season_match else None
        if start_month is None or end_month is None:
            raise SourceArgumentNotFound(
                "district", self._district, "could not read the collection season"
            )

        day1_wd, day2_wd, winter_wd = districts[self._district]
        return [
            {
                "summer_days": (day1_wd, day2_wd),
                "winter_day": winter_wd,
                "season": (
                    start_month,
                    int(season_match.group(2)),
                    end_month,
                    int(season_match.group(4)),
                ),
            }
        ]
