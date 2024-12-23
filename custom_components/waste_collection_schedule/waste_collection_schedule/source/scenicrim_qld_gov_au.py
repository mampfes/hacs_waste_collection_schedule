import csv
import logging
from datetime import datetime, timedelta

import requests
from dateutil.rrule import FR, MO, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Scenic Rim Regional Council"
DESCRIPTION = "Source for scenicrim.qld.gov.au services for Scenic Rim Regional Council"
URL = "https://scenicrim.qld.gov.au"
TEST_CASES = {
    "Red Week": {
        "address": "The Old Avocado Farm 77A Long Road TAMBORINE MOUNTAIN  QLD 4272",
    },
    "Blue Week": {
        "address": "Elysian Fields 2/3043 Beaudesert-Nerang Road WONGLEPONG  QLD 4275"
    },
}
API_URL = "https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv"
ICON_MAP = {
    "GENERAL WASTE": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
}
HEADERS: dict = {
    "user-agent": "Mozilla/5.0",
    # "accept": "application/json, text/plain, */*",
}
DAYS: dict = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
}
WEEKDAYS: list = [MO, TU, WE, TH, FR]
START_DATES: dict = {  # taken from https://www.scenicrim.qld.gov.au/downloads/file/6551/your-waste-bins-and-facilities-guide
    "BLUE": datetime(2024, 12, 2, 0, 0, 0),  # known Monday in a Red Week
    "RED": datetime(2024, 12, 9, 0, 0, 0),  # known Monday in a Blue Week
}
NOW: datetime = datetime.now()
START_DATE: datetime = NOW + timedelta(days=-1)
END_DATE: datetime = NOW + timedelta(days=14)

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Your address as it appears in the _Street_Address_ column of the csv file used by the website. Addresses contain both single-space and double-space character sequences and these need to be preserved. The csv file can be found at (https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv ",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "address": "Your address as it appears in the csf file used by the website",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "address": "Your address as it appears in the csf file used by the website",
    },
}

# ### End of arguments affecting the configuration GUI ####


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, address: str):
        self._address: str = address

    def generate_dates(self, weekday: int, date_start: datetime, interval: int) -> list:
        rr = rrule(
            freq=WEEKLY,
            interval=interval,
            wkst=MO,
            byweekday=(weekday),
            dtstart=date_start,
        )
        dates = [dt for dt in rr.between(date_start, END_DATE, inc=True)]
        return dates

    def create_collection(self, entries: list, title: str, dates: list) -> Collection:
        for dt in dates:
            entries.append(
                Collection(
                    date=dt.date(),
                    t=title,
                    icon=ICON_MAP.get(title),
                )
            )
        return entries

    def fetch(self):
        s = requests.Session()

        # get master schedule from website
        csv_file = s.get(
            "https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv"
        )
        csv_decoded = csv_file.content.decode("utf-8")
        address_list: list = csv.reader(csv_decoded.splitlines(), delimiter=",")
        address_list = [
            [element.upper() for element in address] for address in address_list
        ]

        # extract service day and recycling code
        for item in address_list:
            if self._address.upper() in item[0]:
                service_day: str = item[-2]
                recycling_code: str = item[-1].split(" ")[1]

        entries = []

        # generate general waste dates
        service_days = self.generate_dates(DAYS[service_day], START_DATE, 1)
        service_days = [["GENERAL WASTE", day] for day in service_days]
        # generate recycling dates
        recycling_days = self.generate_dates(
            DAYS[service_day], START_DATES[recycling_code], 2
        )
        recycling_days = [["RECYCLING", day] for day in recycling_days]
        # combine to create collection scheduke
        collection_days: list = service_days + recycling_days

        for item in collection_days:
            entries.append(
                Collection(
                    date=item[1].date(),
                    t=item[0],
                    icon=ICON_MAP.get(item[0]),
                )
            )

        return entries
