import datetime
from typing import Mapping, Optional

import requests
from bs4 import BeautifulSoup, Tag
from dateutil import parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Royal Borough Of Greenwich"
DESCRIPTION = "Source for services from the Royal Borough Of Greenwich"
URL = "https://www.royalgreenwich.gov.uk/"
TEST_CASES = {
    "address": {"address": "25 - Tizzard Grove - London - SE3 9DH"},
    "houseNumber": {"post_code": "SE9 5AW", "house": "11"},
    "alternativeWeek": {"address": "32 - Glenlyon Road - London - SE9 1AJ"},
}

ADDRESS_SEARCH_URL = "https://www.royalgreenwich.gov.uk/site/custom_scripts/apps/waste-collection/source.php"


DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
ICON_MAP = {
    "recycling": "mdi:recycle",
    "garden": "mdi:leaf",
    "food": "mdi:food-apple",
}

# ### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Using a browser, go to [royalgreenwich.gov.uk](https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/100/find_your_bin_collection_day). "
    'Find the collection day and the first bold text in the message below the search bar (right after "At" and before ":") is your address, use it as-is.'
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "post_code": "Postcode",
        "house": "House number or name",
        "address": "Full address",
    }
}

# ### End of arguments affecting the configuration GUI ####

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
}


class Source:
    def __init__(
        self,
        post_code: Optional[str] = None,
        house: Optional[str] = None,
        address: Optional[str] = None,
    ):
        self._post_code = post_code
        self._house = house
        self._address = address

    def _find_address(self) -> str:
        if not self._post_code:
            raise SourceArgumentRequired(
                "post_code", "postcode is required if address is not provided"
            )
        term_list = [self._post_code]
        if self._house:
            term_list.append(self._house)

        s = requests.Session()
        s.headers.update(HEADERS)

        search_term = " ".join(term_list)
        r = s.get(ADDRESS_SEARCH_URL, params={"term": search_term})
        r.raise_for_status()

        addresses = r.json()

        if len(addresses) > 1:
            raise SourceArgAmbiguousWithSuggestions("house", self._house, addresses)

        if len(addresses) == 0:
            raise SourceArgumentNotFound("house", self._house)

        return addresses[0]

    def _get_black_top_bin_next_collection_date(
        self, week_name: str, this_week_collection_date: datetime.date
    ) -> datetime.date:
        s = requests.Session()
        s.headers.update(HEADERS)

        r = s.get(
            "https://www.royalgreenwich.gov.uk/info/200171/recycling_and_rubbish/2436/black_top_bin_collections"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        black_top_bin_schedule_table = soup.find("table")
        if not isinstance(black_top_bin_schedule_table, Tag):
            raise Exception("Could not find address form")

        headers = black_top_bin_schedule_table.find_all("th")
        week_column_index = list(map(lambda h: h.text, headers)).index(week_name)
        if week_column_index < 0:
            raise Exception("Cannot find black top bin collection weeks")

        # e.g. Monday 1 January to Friday 5 January
        first_week_dates_range_str: str = (
            black_top_bin_schedule_table.find("tbody")
            .find("tr")
            .find_all("td")[week_column_index]
            .text
        )

        first_week_date = parser.parse(
            first_week_dates_range_str.split(" to ")[0]
        ).date()

        # we assume that this "first_week_date" is always Monday (as per schedule)
        first_week_collection_date = first_week_date + datetime.timedelta(
            this_week_collection_date.isoweekday() - 1
        )
        return (
            this_week_collection_date + datetime.timedelta(weeks=1)
            if (this_week_collection_date - first_week_collection_date).days % 14
            else this_week_collection_date
        )

    def _get_bank_holiday_overrides(self) -> Mapping[datetime.date, datetime.date]:
        s = requests.Session()
        s.headers.update(HEADERS)

        r = s.get(
            "https://www.royalgreenwich.gov.uk/recycling-and-rubbish/bins-and-collections/bank-holiday-collection-dates"
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        bank_holiday_bin_collection_table = soup.find("table")
        if (
            not isinstance(bank_holiday_bin_collection_table, Tag)
            or len(bank_holiday_bin_collection_table.find_all("th")) < 2
        ):
            # skip generating bank holiday overrides if the table is empty or of invalid format
            return {}

        result = {}
        for row in bank_holiday_bin_collection_table.find("tbody").find_all("tr"):
            row_dates = row.find_all("td")
            if len(row_dates) < 2:
                continue

            from_date = parser.parse(row_dates[0].text).date()
            to_date = parser.parse(row_dates[1].text).date()

            result[from_date] = to_date

        return result

    def _correct_collection_date(
        self,
        collection_date: datetime.date,
        bank_holiday_overrides: Mapping[datetime.date, datetime.date],
    ) -> datetime.date:
        return bank_holiday_overrides.get(collection_date, collection_date)

    def fetch(self) -> list[Collection]:
        if not self._address:
            self._address = self._find_address()

        s = requests.Session()
        s.headers.update(HEADERS)

        r = s.get(
            "https://www.royalgreenwich.gov.uk/site/custom_scripts/apps/waste-collection/ajax-response-uprn.php",
            params={"address": self._address},
        )
        r.raise_for_status()

        # even if address is part of the borough it doesn't mean they will provide data for it
        # e.g. for flats they explicitly mentioned to contact management company instead
        # so in this case address can be found in previous steps, but there is no data for it and this error is returned
        if r.text == "ADDRESS_NOT_FOUND":
            raise Exception(f"No data found for address '{self._address}'")

        data = r.json()

        collection_day = data["Day"]
        black_top_bin_week = data["Frequency"]

        today = datetime.date.today()
        collection_day_index = DAYS.index(collection_day.upper()) + 1
        this_week_collection_date = today + datetime.timedelta(
            (collection_day_index - today.isoweekday()) % 7
        )

        next_food_collection_date = self._get_black_top_bin_next_collection_date(
            black_top_bin_week, this_week_collection_date
        )

        bank_holiday_overrides = self._get_bank_holiday_overrides()

        weeks_to_generate = 10

        recycling_collections = [
            Collection(
                date=self._correct_collection_date(
                    this_week_collection_date + datetime.timedelta(weeks=i),
                    bank_holiday_overrides,
                ),
                t="recycling",
                icon=ICON_MAP.get("recycling"),
            )
            for i in range(weeks_to_generate)
        ]

        garden_collections = [
            Collection(
                date=self._correct_collection_date(
                    this_week_collection_date + datetime.timedelta(weeks=i),
                    bank_holiday_overrides,
                ),
                t="garden",
                icon=ICON_MAP.get("garden"),
            )
            for i in range(weeks_to_generate)
        ]

        food_collections = [
            Collection(
                date=self._correct_collection_date(
                    next_food_collection_date + datetime.timedelta(weeks=i * 2),
                    bank_holiday_overrides,
                ),
                t="food",
                icon=ICON_MAP.get("food"),
            )
            for i in range(int(weeks_to_generate / 2))
        ]

        return recycling_collections + garden_collections + food_collections
