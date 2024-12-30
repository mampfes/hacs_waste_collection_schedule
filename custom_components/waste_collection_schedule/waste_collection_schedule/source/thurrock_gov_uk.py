from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

# import rrule
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule, weekday
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

WEEKDAYS = {
    "monday": MO,
    "tuesday": TU,
    "wednesday": WE,
    "thursday": TH,
    "friday": FR,
    "saturday": SA,
    "sunday": SU,
}

TITLE = "Thurrock"
DESCRIPTION = "Source for Thurrock."
URL = "https://www.thurrock.gov.uk/"
TEST_CASES = {
    "Camden Close Chadwell St Mary": {
        "street": "Camden Close",
        "town": "Chadwell St Mary",
    }
}


ICON_MAP = {
    "Brown": "mdi:leaf",
    "Blue": "mdi:package-variant",
    "Green": "mdi:recycle",
    "Grey": "mdi:recycle",
    "Green/Grey": "mdi:recycle",
}


API_URL = "https://www.thurrock.gov.uk/household-bin-collection-days/household-bin-collection-weeks"
STREETS_URL = (
    "https://www.thurrock.gov.uk/household-bin-collection-days/street-names-{start}"
)


class Source:
    def __init__(self, street: str, town: str):
        self._street: str = street
        self._town: str = town
        self._day: weekday | None = None
        self._round: str | None = None

    def fetch_day(self):
        if len(self._street) == 0:
            raise SourceArgumentRequired(
                "street",
                "Please provide a street name",
            )
        r = requests.get(
            STREETS_URL.format(start=self._street[0].lower()), verify=False
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text.replace("\xa0", " "), "html.parser")
        table = soup.select_one("table")
        if not table:
            raise Exception("street, town Table not found")
        towns = []
        streets = []
        day_str = None
        town_match = False
        street_match = False

        for row in table.select("tr")[1:]:
            cells = row.select("td")
            if len(cells) != 3:
                continue
            street, town = cells[0].text.strip().split(", ")
            street = street
            town = town

            towns.append(town.strip().casefold())
            streets.append(street.strip().casefold())
            if self._street.lower().casefold() in street.lower().casefold():
                street_match = True
            if self._town.lower().casefold() in town.lower().casefold():
                town_match = True
            if street_match and town_match:
                day_str = cells[1].text.strip()
                self._round = cells[2].text.strip()
                break
        if not day_str:
            if town_match:
                raise SourceArgumentNotFoundWithSuggestions(
                    "street",
                    self._street,
                    streets,
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "town",
                self._town,
                towns,
            )

        if day_str.lower() not in WEEKDAYS:
            raise Exception(f"Day ({day_str}) not a valid weekday")
        self._day = WEEKDAYS[day_str.lower()]

    def parse_date_without_year(self, date_str: str) -> date:
        now = datetime.now()

        try:
            date_1 = datetime.strptime(date_str + f" {now.year}", "%d %B %Y").date()
        except ValueError:
            date_1 = datetime.strptime(date_str + f" {now.year + 1}", "%d %B %Y").date()
        try:
            date_2 = datetime.strptime(date_str + f" {now.year + 1}", "%d %B %Y").date()
        except ValueError:
            date_2 = date_1

        try:
            date_3 = datetime.strptime(date_str + f" {now.year - 1}", "%d %B %Y").date()
        except ValueError:
            date_3 = date_1

        return sorted([date_1, date_2, date_3], key=lambda x: abs(x - now.date()))[0]

    def parse_date_range(
        self, range_str: str, not_before: date | None = None
    ) -> tuple[date, date]:
        now = datetime.now()
        start, end = range_str.split(" to ")
        start_date = self.parse_date_without_year(start)
        end_date = self.parse_date_without_year(end)

        end_date = datetime.strptime(end + f" {now.year}", "%d %B %Y").date()
        if start_date.month == 12 and end_date.month == 1:
            end_date = end_date.replace(year=start_date.year + 1)

        if not_before is None or start_date < not_before:
            start_date = start_date.replace(year=start_date.year + 1)
            end_date = end_date.replace(year=end_date.year + 1)

        return start_date, end_date

    def fetch(self) -> list[Collection]:
        if self._day is None or self._round is None:
            self.fetch_day()
            assert self._day is not None
            assert self._round is not None

        # get json file
        r = requests.get(API_URL, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text.replace("\xa0", " "), "html.parser")
        table = soup.select_one("table")
        if not table:
            raise Exception("Collection table not found")

        end_date = None
        entries = []

        for tr in table.select("tr")[1:]:
            cells = tr.select("td")
            if len(cells) != 3:
                raise Exception("Invalid table format")
            start_date, end_date = self.parse_date_range(
                cells[0].text.strip(), not_before=end_date
            )

            bin_text = cells[(1 if self._round == "A" else 2)].text.strip()
            bins = bin_text.split(" and ")

            for bin in bins:
                for col_date in rrule(
                    WEEKLY,
                    dtstart=start_date,
                    until=end_date,
                    byweekday=self._day,
                ):
                    entries.append(
                        Collection(
                            date=col_date.date(),
                            t=bin,
                            icon=ICON_MAP.get(bin),
                        )
                    )

        return entries
