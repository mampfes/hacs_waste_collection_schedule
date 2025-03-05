import requests
from datetime import date, timedelta
from icalendar import Calendar
from waste_collection_schedule import Collection

TITLE = "Municipality of Dinhard Waste Collection"
DESCRIPTION = "Waste collection schedule for the municipality of Dinhard (regular waste, organic waste, paper/cardboard)"
URL = "https://www.dinhard.ch/verwaltung/veranstaltungen.html/167"
TEST_CASES = {
    "Dinhard": {}
}

ICS_URLS = {
    "Grüngutabfuhr": "https://www.dinhard.ch/route/core-iCalendar-generate/entityid/1507/entitytypeid/215",
    "Altpapier/Karton": "https://www.dinhard.ch/route/core-iCalendar-generate/entityid/2741/entitytypeid/215",
    "Verschiebedatum Kehricht": "https://www.dinhard.ch/route/core-iCalendar-generate/entityid/2745/entitytypeid/215"
}

FEIERTAGE = [
    date(2025, 1, 1),   # New Year's Day
    date(2025, 4, 18),  # Good Friday
    date(2025, 4, 21),  # Easter Monday
    date(2025, 5, 29),  # Ascension Day
    date(2025, 6, 9),   # Whit Monday
    date(2025, 12, 25), # Christmas
    date(2025, 12, 26)  # St. Stephen's Day
]

class Source:
    def __init__(self, **_):
        pass

    def fetch(self):
        entries = []

        today = date.today()
        monday = self.next_weekday(today, 0)

        for _ in range(52):
            if monday in FEIERTAGE:
                rescheduled_date = self.get_verschiebedatum(monday)
                if rescheduled_date:
                    entries.append(Collection(date=rescheduled_date, t="Regular Waste Collection (rescheduled)"))
                else:
                    entries.append(Collection(date=monday, t="Regular Waste Collection (holiday, not rescheduled)"))
            else:
                entries.append(Collection(date=monday, t="Regular Waste Collection"))

            monday += timedelta(weeks=1)

        for name, url in ICS_URLS.items():
            for collection in self.fetch_from_ics(url, name):
                entries.append(collection)

        return entries

    def fetch_from_ics(self, url, waste_type_filter):
        response = requests.get(url)
        response.raise_for_status()
        calendar = Calendar.from_ical(response.content)
        collections = []
        for event in calendar.walk("vevent"):
            event_date = event.get("dtstart").dt
            summary = str(event.get("summary"))
            if waste_type_filter in summary:
                collections.append(Collection(date=event_date, t=summary))
        return collections

    def get_verschiebedatum(self, holiday_date):
        response = requests.get(ICS_URLS["Verschiebedatum Kehricht"])
        response.raise_for_status()
        calendar = Calendar.from_ical(response.content)
        for event in calendar.walk("vevent"):
            event_date = event.get("dtstart").dt
            if event_date == holiday_date:
                return event_date
        return None

    def next_weekday(self, start_date, weekday):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)