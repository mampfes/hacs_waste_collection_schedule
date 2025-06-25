import json
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Appfuhr.de Ammerland"
DESCRIPTION = "Source for Appfuhr.de waste collection dates"
URL = "https://www.awb-ammerland.de"
COUNTRY = "de"
TEST_CASES = {
    "Default": {"strid": 1},
}

API_URL = "https://firebasestorage.googleapis.com/v0/b/abfall-ammerland.appspot.com/o/and%2F5%2Fawbapp.json?alt=media"


class Source:
    def __init__(self, strid: int):
        self._strid = strid

    def _calculate_dates(self, start_date: datetime, days_offset: int, is_even_week: bool) -> list[datetime]:
        end_date = datetime(datetime.now().year, 12, 31)
        current_date = start_date + timedelta(days=days_offset)
        if is_even_week:
            if current_date.isocalendar().week % 2 != 0:
                current_date += timedelta(weeks=1)
        else:
            if current_date.isocalendar().week % 2 == 0:
                current_date += timedelta(weeks=1)

        dates = []
        interval = 14
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=interval)
        return dates

    def _get_waste_dates(self, waste_entries: list[dict], paper_data: list[dict]) -> list[tuple[str, datetime]]:
        collection_days = []
        for entry in waste_entries:
            year = entry["jahr"] + 2000
            start_date = datetime(year, 1, 1)

            if entry.get("resttag"):
                dates = self._calculate_dates(start_date, entry["resttag"] - 1, entry["restgu"])
                collection_days.extend([("Restmüll", d) for d in dates])
            if entry.get("biotag"):
                dates = self._calculate_dates(start_date, entry["biotag"] - 1, entry["biogu"])
                collection_days.extend([("Bioabfall", d) for d in dates])
            if entry.get("werttag"):
                dates = self._calculate_dates(start_date, entry["werttag"] - 1, entry["wertgu"])
                collection_days.extend([("Gelber Sack", d) for d in dates])
            if entry.get("papier"):
                paper_dates = [
                    datetime.strptime(p["datum"], "%Y-%m-%d")
                    for p in paper_data
                    if p.get("papier") == entry["papier"]
                ]
                collection_days.extend([("Papier", d) for d in paper_dates])
        return collection_days

    def fetch(self):
        r = requests.get(API_URL)
        r.raise_for_status()
        raw = r.text
        blocks = raw.split("##")
        data = [json.loads(b) for b in blocks if b.strip()]

        waste_entries: list[dict] | None = None
        paper_data: list[dict] | None = None

        # the API is a concatenation of multiple JSON lists. Unfortunately
        # their ordering changed in the past, therefore we search for the
        # required lists dynamically instead of relying on fixed indexes.
        for arr in data:
            if not isinstance(arr, list) or not arr or not isinstance(arr[0], dict):
                continue
            if waste_entries is None and "strid" in arr[0] and "jahr" in arr[0]:
                waste_entries = [e for e in arr if e.get("strid") == self._strid]
                continue
            if paper_data is None and "papier" in arr[0] and "datum" in arr[0]:
                paper_data = arr
                continue

        if waste_entries is None:
            raise ValueError("Could not locate waste schedule data in API result")
        if paper_data is None:
            # If no paper data is provided the calendar would miss paper
            # collections. To be robust we continue with an empty list.
            paper_data = []

        collection_days = self._get_waste_dates(waste_entries, paper_data)

        entries = [Collection(d[1].date(), d[0]) for d in collection_days]
        return sorted(entries, key=lambda x: x.date)
