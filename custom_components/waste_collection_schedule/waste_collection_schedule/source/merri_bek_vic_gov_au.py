from datetime import datetime, timedelta
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Merri-bek City Council"
DESCRIPTION = "Source for Merri-bek City Council (VIC) rubbish collection."
URL = "https://www.merri-bek.vic.gov.au"

TEST_CASES = {
    "Monday": {"address": "1 Widford Street Glenroy 3046"},
    "Tuesday": {"address": "1 Gaffney Street Coburg 3058"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Green": "mdi:leaf",
}

class Source:
    def __init__(self, address):
        self.address = address

    def fetch(self):
        # Step 1 – Query WasteServices4Bin for this address
        url = "https://services6.arcgis.com/8L5sOwfzTAvcvQur/ArcGIS/rest/services/WasteServices4Bin/FeatureServer/0/query"
        params = {
            "where": f"EZI_Address LIKE '{self.address}%'",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()

        features = data.get("features")
        if not features:
            raise Exception("Address not found")

        attr = features[0]["attributes"]

        day_name = attr["Day"]  # e.g. "Monday"
        glass_week = attr.get("GlassWeek", 1) or 1  # often 1 or 2

        # Step 2 – Find the next 10 collection dates based on weekday
        weekday_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2,
            "Thursday": 3, "Friday": 4,
        }
        if day_name not in weekday_map:
            raise Exception(f"Unexpected day value: {day_name}")

        today = datetime.now().date()
        day_num = weekday_map[day_name]

        # Find the next bin day (this week or next)
        days_ahead = (day_num - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7  # always look forward
        first_collection = today + timedelta(days=days_ahead)

        entries = []

        # Step 3 – Generate schedule forward 12 weeks
        for i in range(12):
            current_date = first_collection + timedelta(weeks=i)
            # Weekly bins
            entries.append(Collection(date=current_date, t="Rubbish", icon=ICON_MAP["Rubbish"]))
            entries.append(Collection(date=current_date, t="Green", icon=ICON_MAP["Green"]))

            # Fortnightly recycling (alternate weeks)
            if i % 2 == 0:
                entries.append(Collection(date=current_date, t="Recycling", icon=ICON_MAP["Recycling"]))

            # Glass based on GlassWeek offset
            if (i % 2) == ((glass_week - 1) % 2):
                entries.append(Collection(date=current_date, t="Glass", icon=ICON_MAP["Glass"]))

        return entries
