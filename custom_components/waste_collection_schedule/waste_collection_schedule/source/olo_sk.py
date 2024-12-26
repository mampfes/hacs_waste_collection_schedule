import datetime
from waste_collection_schedule import Collection
import requests

TITLE = "OLO"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for olo.sk"  # Describe your source
# Insert url to service homepage. URL will show up in README.md and info.md
URL = "https://www.olo.sk"
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "Jantarova 47": {"street": 'Jantarova 47', "registrationNumber": '2441788'},
    "Jasovska 8": {"street": 'Jasovska 8', "registrationNumber": '1353013'},
    "Rovniankova 5": {"street": 'Rovniankova 5', "registrationNumber": ''},
}

API_URL = "https://olo-strapi-meilisearch.bratislava.sk/indexes/waste-collection-day/search"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "KITCHEN": "mdi:coutertop",
}

WEKDAYS = {
    "pondelok": "Monday",
    "utorok": "Tuesday",
    "streda": "Wednesday",
    "štvrtok": "Thursday",
    "piatok": "Friday",
    "sobota": "Saturday",
    "nedeľa": "Sunday"
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION"
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "street": "Street name",
        "registrationNumber": "Registration number"
    }
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "street": "Enter street name",
        "registrationNumber": "Enter registration number"
    }
}

#### End of arguments affecting the configuration GUI ####


class Source:
    # argX correspond to the args dict in the source configuration
    def __init__(self, street: str, registrationNumber: str):
        self._street = street
        self._registrationNumber = registrationNumber

    def parseDates(self, dates_str: str) -> list[datetime.date]:
        dates = dates_str.split(";")
        dates = [date.strip() for date in dates]
        dates = [date for date in dates if date]
        return [datetime.datetime.strptime(date, "%d.%m.%Y").date() for date in dates]

    def fetchWasteType(self, waste_type: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "authorization": "Bearer ae84ae0982c2162a81eb253765ceaa8593abd9105c71954cf5c9620b0178cbb6"
        }

        params = {
            "q": self._street,
            "limit": 100,
            "offset": 0,
            "sort": ["waste-collection-day.address:asc"],
            "filter": ["type = \"waste-collection-day\"", "waste-collection-day.type = \"" + waste_type + "\""]
        }

        response = requests.post(API_URL, json=params, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        items = data.get("hits", [])
        return [item.get("waste-collection-day", {}) for item in items]

    def getRecycableWaste(self) -> list[Collection]:
        items = self.fetchWasteType("vrecovyZ")
        if not items:
            return []

        first_item = items[0]

        collection_dates_str = first_item.get("collectionDates")
        if not collection_dates_str:
            return []

        collection_dates = self.parseDates(collection_dates_str)

        return [Collection(
            date=date,
            t="Recycable Waste",
            icon=ICON_MAP.get("RECYCLE")
        ) for date in collection_dates]

    def generate_dates(self, weekdays: list[str], is_even_week: bool) -> list[datetime.date]:
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=90)
        dates = []

        current_date = today
        while current_date <= end_date:
            week_number = current_date.isocalendar()[1]
            if (is_even_week and week_number % 2 == 0) or (not is_even_week and week_number % 2 != 0):
                if current_date.strftime("%A") in weekdays:
                    dates.append(current_date)
            current_date += datetime.timedelta(days=1)
        return dates

    def getDomesticWaste(self) -> list[Collection]:
        items = self.fetchWasteType("zkoD")
        if not items:
            return []

        if self._registrationNumber:
            items = [item for item in items if item.get(
                "registrationNumber") == self._registrationNumber]
            if not items:
                return []

        first_item = items[0]

        evenWeek_str = first_item.get("evenWeek", "")
        oddWeek_str = first_item.get("oddWeek", "")

        evenWeek = [day.strip()
                    for day in evenWeek_str.split(",") if day.strip()]
        oddWeek = [day.strip()
                   for day in oddWeek_str.split(",") if day.strip()]

        evenWeek = [WEKDAYS[day] for day in evenWeek]
        oddWeek = [WEKDAYS[day] for day in oddWeek]

        evenWeek_dates = self.generate_dates(evenWeek, True)
        oddWeek_dates = self.generate_dates(oddWeek, False)

        collection_dates = evenWeek_dates + oddWeek_dates
        collection_dates.sort()

        return [Collection(
            date=date,
            t="Domestic Waste",
            icon=ICON_MAP.get("DOMESTIC")
        ) for date in collection_dates]

    def fetch(self) -> list[Collection]:
        recycable_waste = self.getRecycableWaste()
        domestic_waste = self.getDomesticWaste()

        entries = recycable_waste + domestic_waste

        if not entries:
            raise Exception("No waste data found")

        return entries
