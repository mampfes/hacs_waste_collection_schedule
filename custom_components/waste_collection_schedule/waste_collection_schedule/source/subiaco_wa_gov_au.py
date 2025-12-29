import datetime
from waste_collection_schedule import Collection

TITLE = "City of Subiaco"
DESCRIPTION = "Source for City of Subiaco, WA waste collection using Area and Weekday."
URL = "https://www.subiaco.wa.gov.au"
COUNTRY = "au"

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

TEST_CASES = {
    "Area 1 Monday": {"area": 1, "day_of_week": "Monday"},
    "Area 2 Wednesday": {"area": 2, "day_of_week": "Wednesday"},
}

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "Recycling": "mdi:recycle",
    "General Waste": "mdi:trash-can",
}

class Source:
    def __init__(self, area: int, day_of_week: str):
        self._area = int(area)
        self._day_of_week = day_of_week.strip().capitalize()
        if self._day_of_week not in WEEKDAYS:
            raise ValueError(f"Invalid day_of_week. Must be one of: {', '.join(WEEKDAYS)}")

    def fetch(self):
        entries = []
        now = datetime.date.today()
        # Fetching a window of 30 days back and 365 days forward
        start_date = now - datetime.timedelta(days=30)
        
        # Reference Dates (Recycling Mondays) from 2024/25 Calendar
        # Area 1: Recycling Monday June 24, 2024
        # Area 2: Recycling Monday July 1, 2024
        ref_rec_area1 = datetime.date(2024, 6, 24)
        ref_rec_area2 = datetime.date(2024, 7, 1)
        ref_base = ref_rec_area1 if self._area == 1 else ref_rec_area2

        target_weekday = WEEKDAYS.index(self._day_of_week)

        for i in range(0, 400):
            d = start_date + datetime.timedelta(days=i)
            
            if d.weekday() == target_weekday:
                # Basic Holiday Offset Logic (e.g., Christmas/New Year 2025)
                # Subiaco pushes collections forward by 1 day during these weeks
                collection_date = d
                if d in [datetime.date(2025, 12, 25), datetime.date(2025, 12, 26), datetime.date(2026, 1, 1), datetime.date(2026, 1, 26), datetime.date(2026, 4, 3) ]:
                    collection_date += datetime.timedelta(days=1)

                # FOGO: Weekly
                entries.append(Collection(date=collection_date, t="FOGO", icon=ICON_MAP.get("FOGO")))
                
                # Recycling vs General Waste: Fortnightly rotation
                delta_weeks = (d - ref_base).days // 7
                if delta_weeks % 2 == 0:
                    entries.append(Collection(date=collection_date, t="Recycling", icon=ICON_MAP.get("Recycling")))
                else:
                    entries.append(Collection(date=collection_date, t="General Waste", icon=ICON_MAP.get("General Waste")))

        return entries