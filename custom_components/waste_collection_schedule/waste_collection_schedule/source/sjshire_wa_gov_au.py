from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Shire of Serpentine Jarrahdale"
DESCRIPTION = "Source for www.sjshire.wa.gov.au Waste Collection Services"
URL = "https://www.sjshire.wa.gov.au"
API_URL = "https://maps.sjshire.wa.gov.au/IntraMaps22B/ApplicationEngine/Integration/api/search"

TEST_CASES = {
    "Monday": {
        "address": "5 Pingaring Court BYFORD WA 6122",
        "predict": True,
    },
    "Tuesday": {"address": "865 South Western Highway BYFORD WA 6122"},
    "Wednesday": {"address": "701 Jarrahdale Road JARRAHDALE WA 6124"},
    "Thursday": {"address": "6 Paterson Street MUNDIJONG WA 6123"},
    "Friday": {"address": "1548 Kargotich Road MARDELLA WA 6125"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}


class Source:
    def __init__(self, address, predict=False):
        self._address = address
        if not isinstance(predict, bool):
            raise Exception("'predict' must be a boolean value")
        self._predict = predict

    def get_weekday_date(self, target_day, week):
        # Dictionary to convert day names to numbers (0 = Monday, 6 = Sunday)
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        today = datetime.now()
        current_weekday = today.weekday()
        target_weekday = weekdays[target_day]
        # Calculate days difference
        days_difference = target_weekday - current_weekday

        # Adjust for "this week" vs "next week"
        if week == "next":
            days_difference += 7
        elif week == "this" and days_difference < 0:
            days_difference += 14
        elif week == "this":
            days_difference += 0

        target_date = today + timedelta(days=days_difference)
        return target_date

    def parse_collection_day(self, day_string):
        # Split the string into day and week
        parts = day_string.split()
        day = parts[0]  # e.g., 'thursday'

        # Determine if it's next week
        if "next" in day_string:
            week = "next"
        elif "this" in day_string:
            week = "this"
        else:
            week = ""

        return self.get_weekday_date(day, week)

    def collect_dates(self, start_date, weeks):
        dates = []
        dates.append(start_date)
        for _ in range(1, 4 // weeks):
            start_date = start_date + timedelta(days=(weeks * 7))
            dates.append(start_date)
        return dates

    def fetch(self):
        entries = []
        # initiate a session

        payload = {}
        params = {
            "configId": "00000000-0000-0000-0000-000000000000",
            "form": "de2aecaf-1e4d-4d25-8146-b0f0109aa458",
            "fields": self._address,
        }
        headers = {"Authorization": "apikey 58383723-1396-43cc-a5cf-722e786208c6"}

        # search for the address
        r = requests.get(API_URL, headers=headers, data=payload, params=params)
        r.raise_for_status()
        search_json = r.json()

        if len(search_json) == 0:
            raise Exception("address not found")
        elif len(search_json) >= 1:  # there's one or more, so filter the exact match
            for entry in search_json:
                for item in entry:
                    if item["name"] == "Address" and item["value"] == self._address:
                        match = entry
                        break

        fields_dict = {item["name"]: item["value"] for item in match}

        params = {
            "configId": "00000000-0000-0000-0000-000000000000",
            "form": "a51626b7-3892-44f4-9fba-b0264486bda5",
            "fields": fields_dict.get("mapkey") + "," + fields_dict.get("dbkey"),
        }

        r = requests.get(API_URL, headers=headers, data=payload, params=params)
        r.raise_for_status()

        fields_json = r.json()[0]

        data_dict = {item["name"]: item for item in fields_json}

        day_rubbish = data_dict.get("WasteCollectionDay")["value"].lower()
        # date_rubbish = self.parse_collection_day(day_rubbish)
        date_rubbish = datetime.today()
        while date_rubbish.strftime("%A").lower() != day_rubbish:
            date_rubbish = date_rubbish + timedelta(days=1)

        day_recycling = data_dict.get("RecycleDay")["value"].lower()
        date_recycling = self.parse_collection_day(day_recycling)

        if self._predict:
            # get the dates for every week in the next 4 weeks
            rub_dates = self.collect_dates(date_rubbish.date(), 1)
            # get the dates for every 2nd week
            rec_dates = self.collect_dates(date_recycling.date(), 2)
        else:
            rub_dates = [date_rubbish.date()]
            rec_dates = [date_recycling.date()]

        collections = []

        collections.append({"type": "Rubbish", "dates": rub_dates})
        collections.append({"type": "Recycling", "dates": rec_dates})

        for collection in collections:
            for date in collection["dates"]:
                entries.append(
                    Collection(
                        date=date,
                        t=collection["type"],
                        icon=ICON_MAP.get(collection["type"]),
                    )
                )

        return entries
