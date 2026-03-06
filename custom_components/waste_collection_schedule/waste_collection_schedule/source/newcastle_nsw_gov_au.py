from datetime import date, timedelta
from waste_collection_schedule import Collection

TITLE = "City of Newcastle (NSW)"
DESCRIPTION = "Newcastle (NSW) waste schedule – weekly rubbish; recycling and organics alternate on the collection day."
URL = "https://newcastle.nsw.gov.au/living/waste-and-recycling/collection-services/bin-collection-days"
TAGS = ["nsw", "newcastle", "australia"]

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Organics": "mdi:leaf",
}

# weekday index: Mon=0, Tue=1, ... Sun=6
WEEKDAY_NAME_TO_IDX = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

class Source:
    """
    Args:
      weekday: name or index of the collection weekday (default 'tuesday')
      recycling_seed: ISO date (YYYY-MM-DD) of a known recycling day for your area
                      (organics will be the alternating week)
      start: optional ISO date for schedule start (default: Jan 1 of seed year)
      end:   optional ISO date for schedule end   (default: Dec 31 of seed year)
    Example (Cooks Hill, Area 1 – Tuesday):
      - name: newcastle_nsw_gov_au
        args:
          weekday: tuesday
          recycling_seed: 2025-01-07
    """

    def __init__(self, weekday="tuesday", recycling_seed=None, start=None, end=None):
        if recycling_seed is None:
            raise ValueError("recycling_seed (YYYY-MM-DD) is required")

        # normalise weekday
        if isinstance(weekday, int):
            wd = weekday
        else:
            wd = WEEKDAY_NAME_TO_IDX.get(str(weekday).strip().lower())
        if wd is None or wd < 0 or wd > 6:
            raise ValueError("weekday must be 0–6 or a valid weekday name")
        self.weekday = wd

        # parse dates
        def _parse(d):
            y, m, dd = map(int, str(d).split("-"))
            return date(y, m, dd)

        self.seed = _parse(recycling_seed)

        year = self.seed.year
        self.start = _parse(start) if start else date(year, 1, 1)
        self.end = _parse(end) if end else date(year, 12, 31)

        # sanity: seed must be on the configured weekday
        if self.seed.weekday() != self.weekday:
            raise ValueError("recycling_seed must fall on the configured weekday")

        # organics alternates with recycling (one week offset)
        self.organics_seed = self.seed + timedelta(days=7)

        # (Optional) add public-holiday shifts here if Council publishes them
        self.holiday_shifts = {}  # e.g. {date(2025, 12, 30): date(2025, 12, 31)}

    def _all_weekday_dates(self):
        # first chosen weekday on/after start
        d = self.start + timedelta((self.weekday - self.start.weekday()) % 7)
        while d <= self.end:
            yield d
            d += timedelta(days=7)

    def _fortnightly_from(self, seed):
        d = seed
        while d <= self.end:
            if d >= self.start:
                yield d
            d += timedelta(days=14)

    def _shift_if_holiday(self, d):
        return self.holiday_shifts.get(d, d)

    def fetch(self):
        out = []

        # Weekly: rubbish every configured weekday
        for d in self._all_weekday_dates():
            dd = self._shift_if_holiday(d)
            out.append(Collection(dd, "Rubbish", icon=ICON_MAP["Rubbish"]))

        # Fortnightly: recycling (seed), organics (seed + 7 days)
        for d in self._fortnightly_from(self.seed):
            dd = self._shift_if_holiday(d)
            out.append(Collection(dd, "Recycling", icon=ICON_MAP["Recycling"]))

        for d in self._fortnightly_from(self.organics_seed):
            dd = self._shift_if_holiday(d)
            out.append(Collection(dd, "Organics", icon=ICON_MAP["Organics"]))

        return out
