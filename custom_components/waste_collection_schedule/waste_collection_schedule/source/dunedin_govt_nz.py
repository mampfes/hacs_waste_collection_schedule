import json
import requests

from  datetime import datetime, timedelta
from waste_collection_schedule import Collection

TITLE = "Dunedin District Council"
DESCRIPTION = "Source for Dunedin District Council Rubbish & Recycling collection."
URL = "https://www.dunedin.govt.nz/"
TEST_CASES = {
    # "No Collection": {"address": "3 Farm Road West Berwick"},  # Useful for troubleshooting, elicits a "No Collection" response from website
    "Calendar 1": {"address": "5 Bennett Road Ocean View"},
    "Calendar 2": {"address": "2 Council Street Dunedin"},
    "All Week": {"address": "118 High Street Dunedin"},
    "Collection 'c'": {"address": "2 - 90 Harbour Terrace Dunedin"},
}
DAYS = {
    "Monday" : 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "BLACK BAG": "mdi:trash-can",
    "BLUE BIN": "mdi:bottle-soda",
    "YELLOW BIN": "mdi:recycle",
}

# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, address):
        self._address = str(address).replace(" ", "+").strip()

    def fetch(self):
        # Get collection json
        s = requests.Session()
        r = s.get(
            f"https://www.dunedin.govt.nz/design/rubbish-and-collection-days-search/lookup/_nocache?query={self._address}",
            headers=HEADERS
        )
        r_json = json.loads(r.text)[0]["attributes"]

        # Work out the date of the next collection(s)
        collection_dates = []
        today = datetime.now().date()
        if r_json["collectionDay"] == "No Collection":
            raise Exception("No collection service for that address")
        elif r_json["collectionDay"] == "Today":
            collection_dates.append(today)
        elif r_json["collectionDay"] == "Tomorrow":
            collection_dates.append(today + timedelta(days=1))
        elif r_json["collectionDay"] == "All Week":  # assume this means weekdays only, not weekends
            collection_date = today
            counter = 0 
            while counter <= 7:
                if collection_date.strftime("%A") in "Monday Tuesday Wednesday Thursday Friday":
                    collection_dates.append(collection_date)
                collection_date = collection_date + timedelta(days=1)
                counter +=1
        else:  # find date of next matching weekday
            collection_date = today
            while collection_date.strftime("%A") != r_json["collectionDay"]:
                collection_date = collection_date + timedelta(days=1)
            collection_dates.append(collection_date)

        # Adjust dates impacted by public holidays
        '''
        Note: A json of the public holiday potentially impacting collections can be retrieved from:
        https://www.dunedin.govt.nz/__data/assets/js_file/0005/875336/publicHolidayData.js
        At the time of writing (2023), none of the listed public holidays impact collection days
        so it's not known how to account for any impact on collection day/date.
        '''

        # Now work out which waste types need to be displayed
        '''
        Note: r_json["CurrentWeek"] contains the collection code for the current calendar week.
        If the collection day hasn't passed, then the collection code should be correct.
        If the collection occurred earlier in the week, the collection code needs
        to be switched to next week's collection code.
        The collection codes seem to translate to:
        b -> Blue bin & Black bag
        c -> Blue bin, Yellow bin & Black bag
        y -> Yellow bin & Black bag
        n -> Black bag
        These are likely to change in 2024 when new waste types are introduced, see:
        https://www.dunedin.govt.nz/council/council-projects/waste-futures/the-future-of-rubbish-and-recycling-in-dunedin
        '''
        if r_json["collectionDay"] != "All Week":
            if today.weekday() > DAYS[r_json["collectionDay"]]:  # collection should have happened
                if r_json["CurrentWeek"] == "c":  # not strictly needed, included for completeness
                    r_json["CurrentWeek"] = "c"
                if r_json["CurrentWeek"] == "y":
                    r_json["CurrentWeek"] = "b"
                elif r_json["CurrentWeek"] != "n" and r_json["CurrentWeek"] != "c":
                    r_json["CurrentWeek"] = "y"

        waste_types = []
        if r_json["CurrentWeek"] == "n":
            waste_types.append("Black Bag")
        elif r_json["CurrentWeek"] == "y":
            waste_types.extend(("Black Bag", "Yellow Bin"))
        elif r_json["CurrentWeek"] == "b":
            waste_types.extend(("Black Bag", "Blue Bin"))
        elif r_json["CurrentWeek"] == "c":
            waste_types.extend(("Black Bag", "Yellow Bin", "Blue Bin"))

        # Now build schedule
        entries = []
        for waste in waste_types:
            for schedule in collection_dates:
                entries.append(
                    Collection(
                        date = schedule,
                        t=waste,
                        icon=ICON_MAP.get(waste.upper()),
                    )
                )

        return entries
