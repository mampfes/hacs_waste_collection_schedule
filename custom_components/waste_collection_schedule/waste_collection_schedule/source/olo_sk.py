import datetime
from waste_collection_schedule import Collection
import requests
import re
from waste_collection_schedule.exceptions import SourceArgumentRequired

TITLE = "OLO"
DESCRIPTION = "Source for OLO in Bratislava, Slovakia"
URL = "https://www.olo.sk"
TEST_CASES = {
    "Jantarova 47": {"street": 'Jantarova 47', "registrationNumber": '2441788'},
    "Jasovska 8": {"street": 'Jasovska 8', "registrationNumber": '1353013'},
    "Rovniankova 5": {"street": 'Rovniankova 5', "registrationNumber": ''},
}

ICON_MAP = {
    "Zmesový odpad": "mdi:trash-can",
    "Triedený odpad": "mdi:recycle",
    "Kuchynský odpad": "mdi:coutertop",
}

# The API list names will be probably needed to change by an future update because it looks like OLO creates new list names each year (at least for some waste types)
# To get the list names automatically would require magic as it can be only identified by a human from the web site
API_LIST_NAME = {
    "DOMESTIC": "zkoD",
    "RECYCLE": "vrecovyZ",
    "KITCHEN": "kbro"
}

# Translation of week days from Slovak (OLO API) to English
WEKDAYS = {
    "pondelok": "Monday",
    "utorok": "Tuesday",
    "streda": "Wednesday",
    "štvrtok": "Thursday",
    "piatok": "Friday",
    "sobota": "Saturday",
    "nedeľa": "Sunday"
}

API_URL = "https://olo-strapi-meilisearch.bratislava.sk/indexes/waste-collection-day/search"
# where to look for the api key
API_KEY_REGEX = r'"NEXT_PUBLIC_MEILISEARCH_HOST:",\s*".*?",\s*"(.*?)"'
API_KEY_SOURCE = "https://www.olo.sk/odpad/zistite-si-svoj-odvozovy-den"
API_KEY_JS_BASE = "https://www.olo.sk"
# Fallback API key in case we can't extract it from the source
API_KEY_FALLBACK = "ae84ae0982c2162a81eb253765ceaa8593abd9105c71954cf5c9620b0178cbb6"

#### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name and number",
        "registrationNumber": "OLO registration number"
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Enter street name",
        "registrationNumber": "Enter OLO registration number"
    }
}

#### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, street: str, registrationNumber: str):
        self._street = street
        self._registrationNumber = registrationNumber

    # Parse dates from string list
    def parseDates(self, dates_str: str) -> list[datetime.date]:
        # Split dates by semicolon, trim whitespace and remove empty strings
        dates = dates_str.split(";")
        dates = [date.strip() for date in dates]
        dates = [date for date in dates if date]

        # Convert string dates to datetime objects
        return [datetime.datetime.strptime(date, "%d.%m.%Y").date() for date in dates]

    # Generic function to fetch waste information from API
    def fetchWasteType(self, waste_type: str) -> str:
        # Get api key from the page source
        apiKey = self.findApiKey()
        if not apiKey:
            apiKey = API_KEY_FALLBACK

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "authorization": "Bearer " + apiKey
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
        # 'hits' is a list of items, each item contains 'waste-collection-day' object
        items = data.get("hits", [])
        # return list of 'waste-collection-day' objects so that we can process directly the inside elements in other functions
        return [item.get("waste-collection-day", {}) for item in items]

    # Get recycable waste collection dates
    def getRecycableWaste(self) -> list[Collection]:
        items = self.fetchWasteType(API_LIST_NAME.get("RECYCLE"))
        if not items:
            return []

        first_item = items[0]

        collection_dates_str = first_item.get("collectionDates")
        if not collection_dates_str:
            return []

        collection_dates = self.parseDates(collection_dates_str)

        return [Collection(
            date=date,
            t="Triedený odpad",
            icon=ICON_MAP.get("Triedený odpad")
        ) for date in collection_dates]

    # Generate list of dates based on week days and even/odd week
    def generateDates(self, weekdays: list[str], isEvenWeek: bool, useEvenOdd: bool) -> list[datetime.date]:
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=90)
        dates = []

        current_date = today
        while current_date <= end_date:
            week_number = current_date.isocalendar()[1]
            if (not useEvenOdd) or (isEvenWeek and week_number % 2 == 0) or (not isEvenWeek and week_number % 2 != 0):
                if current_date.strftime("%A") in weekdays:
                    dates.append(current_date)
            current_date += datetime.timedelta(days=1)
        return dates

    # Get domestic waste collection dates
    def getDomesticWaste(self) -> list[Collection]:
        items = self.fetchWasteType(API_LIST_NAME.get("DOMESTIC"))
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

        evenWeek_dates = self.generateDates(evenWeek, True, True)
        oddWeek_dates = self.generateDates(oddWeek, False, True)

        collection_dates = evenWeek_dates + oddWeek_dates
        collection_dates.sort()

        return [Collection(
            date=date,
            t="Zmesový odpad",
            icon=ICON_MAP.get("Zmesový odpad")
        ) for date in collection_dates]

     # Get domestic waste collection dates
    def getKitchenWaste(self) -> list[Collection]:
        items = self.fetchWasteType(API_LIST_NAME.get("KITCHEN"))
        if not items:
            return []

        first_item = items[0]

        weekDays_str = first_item.get("pickupWeekdays", "")
        weekDays = [day.strip()
                    for day in weekDays_str.split(",") if day.strip()]
        weekDays = [WEKDAYS[day] for day in weekDays]
        dates = self.generateDates(weekDays, True, False)
        dates.sort()

        return [Collection(
            date=date,
            t="Kuchynský odpad",
            icon=ICON_MAP.get("Kuchynský odpad")
        ) for date in dates]

    # Find API key in the web page source code
    def findApiKey(self) -> str:
        # get the page source html
        pageSource = requests.get(API_KEY_SOURCE)
        pageSource.raise_for_status()
        pageSource = pageSource.text

        # find all .js references in the html source
        jsRefs = re.findall(r'<script src="([^"]+)"', pageSource)

        # for each .js reference, check if it contains the api key
        for jsRef in jsRefs:
            apiKey = self.parseApiKey(jsRef)
            if apiKey:
                return apiKey

        return ""

    # Extract the api key from a .js file
    def parseApiKey(self, jsRef: str) -> str:
        response = requests.get(API_KEY_JS_BASE + jsRef)
        response.raise_for_status()
        jsSource = response.text

        # find the api key in the .js source code
        match = re.search(API_KEY_REGEX, jsSource)
        if match:
            return match.group(1)
        else:
            return ""

    # Fetch data from source
    def fetch(self) -> list[Collection]:
        if not self._street:
            raise SourceArgumentRequired("street")

        recycable_waste = self.getRecycableWaste()
        domestic_waste = self.getDomesticWaste()
        kitchen_waste = self.getKitchenWaste()

        entries = recycable_waste + domestic_waste + kitchen_waste

        if not entries:
            raise Exception("No waste data found")

        return entries
