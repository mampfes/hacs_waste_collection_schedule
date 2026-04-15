import datetime
from dateutil.easter import easter
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

    def is_holiday(self, dt):
        """
        Check for New Year's, Christmas, and Good Friday with Monday-observed logic.
        """
        year = dt.year
        
        # 1. Good Friday (Dynamic)
        if dt == easter(year) - datetime.timedelta(days=2):
            return True

        # 2. Fixed Dates with 'Following Monday' Rule
        # Only New Year's and Christmas as requested
        for month, day in [(1, 1), (12, 25)]:
            actual_date = datetime.date(year, month, day)
            if actual_date.weekday() == 5:  # Saturday
                observed = actual_date + datetime.timedelta(days=2)
            elif actual_date.weekday() == 6:  # Sunday
                observed = actual_date + datetime.timedelta(days=1)
            else:
                observed = actual_date
            
            if dt == observed:
                return True
        
        return False

    def fetch(self):
        entries = []
        now = datetime.date.today()
        start_date = now - datetime.timedelta(days=30)
        
        # Reference Dates
        ref_rec_area1 = datetime.date(2024, 6, 24)
        ref_rec_area2 = datetime.date(2024, 7, 1)
        ref_base = ref_rec_area1 if self._area == 1 else ref_rec_area2

        target_weekday = WEEKDAYS.index(self._day_of_week)

        for i in range(0, 400):
            d = start_date + datetime.timedelta(days=i)
            
            if d.weekday() == target_weekday:
                collection_date = d
                
                # If the scheduled day is one of the three holidays, push forward by 1 day
                if self.is_holiday(d):
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