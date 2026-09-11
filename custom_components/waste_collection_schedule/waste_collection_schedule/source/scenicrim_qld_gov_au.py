import csv
import logging
from datetime import datetime, timedelta
from difflib import get_close_matches

import requests
from dateutil.rrule import FR, MO, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

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
    "GENERAL WASTE": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
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

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Your address as it appears in the _Street_Address_ column of the csv file used by the website. Case and spacing do not have to match: the register's double spaces and upper-casing are ignored when matching. The csv file can be found at https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv",
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


def _normalise(text: str) -> str:
    """Upper-case and collapse whitespace.

    The register mixes single- and double-space sequences ("1 ACACIA STREET
    BEAUDESERT  QLD 4285"), which previously meant a caller had to reproduce
    that spacing exactly. Comparing on collapsed whitespace removes that trap
    without changing which property matches.
    """
    return " ".join(text.upper().split())


class Source:
    def __init__(self, address: str):
        self._address: str = _normalise(address)

    def generate_dates(
        self, weekday: int, date_start: datetime, interval: int, date_end: datetime
    ) -> list:
        rr = rrule(
            freq=WEEKLY,
            interval=interval,
            wkst=MO,
            byweekday=(weekday),
            dtstart=date_start,
        )
        dates = list(rr.between(date_start, date_end, inc=True))
        return dates

    def fetch(self):
        s = requests.Session()

        # get master schedule from website
        csv_file = s.get(API_URL)
        csv_decoded = csv_file.content.decode("utf-8")
        rows = list(csv.reader(csv_decoded.splitlines(), delimiter=","))
        # Row 0 is the header; every later row is
        # [Street_Address, Street, Street_Locality, Service_Day, Recycle_Week].
        address_list: list = [
            [element.upper() for element in row] for row in rows[1:] if row and row[0]
        ]

        # Extract service day and recycling code. Prefer an exact match on the
        # register address, falling back to a substring match; the register
        # contains addresses that are prefixes of others ("1 SMITH ST" is a
        # substring of "11 SMITH ST"), and the previous loop kept the last
        # match rather than the best one.
        match = None
        substring_match = None
        for item in address_list:
            register_address = _normalise(item[0])
            if register_address == self._address:
                match = item
                break
            if substring_match is None and self._address in register_address:
                substring_match = item
        if match is None:
            match = substring_match

        # No match previously left service_day unbound, so an address that is
        # not in the register raised UnboundLocalError and surfaced as an
        # opaque HTTP 500 instead of telling the user what to enter.
        if match is None or match[-2] not in DAYS:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                # The register holds ~17k addresses; returning all of them
                # would build a several-hundred-kilobyte error message, so
                # only offer the closest candidates.
                get_close_matches(
                    self._address,
                    [item[0] for item in address_list],
                    n=5,
                    cutoff=0.4,
                ),
            )

        service_day: str = match[-2]
        # Recycle_Week reads e.g. "Week1 Red"/"Week2 Blue", but some properties
        # are listed as "Contact Council" instead.
        recycle_week: list = match[-1].split(" ")
        recycling_code: str = recycle_week[1] if len(recycle_week) > 1 else ""

        # set up start/end dates for generate_dates
        now: datetime = datetime.now()
        start_date: datetime = now + timedelta(days=-1)
        end_date: datetime = now + timedelta(days=14)
        # generate general waste dates
        service_days = self.generate_dates(DAYS[service_day], start_date, 1, end_date)
        service_days = [["GENERAL WASTE", day] for day in service_days]
        # generate recycling dates; properties whose Recycle_Week is "Contact
        # Council" are not on the projectable Red/Blue fortnightly cycle, so
        # report general waste only rather than raising a KeyError.
        recycling_days: list = []
        if recycling_code in START_DATES:
            recycling_days = [
                ["RECYCLING", day]
                for day in self.generate_dates(
                    DAYS[service_day], START_DATES[recycling_code], 2, end_date
                )
            ]
        else:
            _LOGGER.info(
                "No recycling week published for '%s' (Recycle_Week is '%s'); "
                "reporting general waste only",
                self._address,
                match[-1],
            )
        # combine to create collection schedule
        collection_days: list = service_days + recycling_days

        entries = []
        for item in collection_days:
            entries.append(
                Collection(
                    date=item[1].date(),
                    t=item[0],
                    icon=ICON_MAP.get(item[0]),
                )
            )

        return entries
