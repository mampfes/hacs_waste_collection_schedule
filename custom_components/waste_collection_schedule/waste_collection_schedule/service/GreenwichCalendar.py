"""GreenwichCalendar retrieval and parsing, using the pipeline HTTP session."""

import datetime
from collections.abc import Mapping
from typing import Any

from bs4 import BeautifulSoup, Tag
from dateutil import parser

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

ADDRESS_SEARCH_URL = "https://www.royalgreenwich.gov.uk/site/custom_scripts/apps/waste-collection/source.php"
DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0"
}


class _CalendarClient:
    _session: Any

    def __init__(
        self,
        post_code: str | None = None,
        house: str | None = None,
        address: str | None = None,
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
        s = self._session
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
        s = self._session
        s.headers.update(HEADERS)
        r = s.get(
            "https://www.royalgreenwich.gov.uk/recycling-and-rubbish/bins-and-collections/black-top-bin-collections"
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        black_top_bin_schedule_table = soup.find("table")
        if not isinstance(black_top_bin_schedule_table, Tag):
            raise ValueError("Could not find address form")
        headers = black_top_bin_schedule_table.find_all("th")
        week_column_index = [h.text for h in headers].index(week_name)
        if week_column_index < 0:
            raise ValueError("Cannot find black top bin collection weeks")
        table_body = black_top_bin_schedule_table.find("tbody")
        if table_body is None:
            raise ValueError("Could not find black top bin collection table body")
        first_row = table_body.find("tr")
        if first_row is None:
            raise ValueError("Could not find black top bin collection table row")
        first_week_dates_range_str = first_row.find_all("td")[week_column_index].text
        first_week_date = parser.parse(
            first_week_dates_range_str.split(" to ")[0]
        ).date()
        first_week_collection_date = first_week_date + datetime.timedelta(
            this_week_collection_date.isoweekday() - 1
        )
        return (
            this_week_collection_date + datetime.timedelta(weeks=1)
            if (this_week_collection_date - first_week_collection_date).days % 14
            else this_week_collection_date
        )

    def _get_bank_holiday_overrides(self) -> Mapping[datetime.date, datetime.date]:
        s = self._session
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
            return {}
        result = {}
        table_body = bank_holiday_bin_collection_table.find("tbody")
        if table_body is None:
            raise ValueError("Could not find bank holiday collection table body")
        for row in table_body.find_all("tr"):
            row_dates = row.find_all("td")
            if len(row_dates) < 2:
                continue
            from_date = parser.parse(row_dates[0].text, fuzzy=True).date()
            to_date = (
                from_date
                if row_dates[1].text == "Collections as normal"
                else parser.parse(row_dates[1].text, fuzzy=True).date()
            )
            result[from_date] = to_date
        return result

    def _correct_collection_date(
        self,
        collection_date: datetime.date,
        bank_holiday_overrides: Mapping[datetime.date, datetime.date],
    ) -> datetime.date:
        return bank_holiday_overrides.get(collection_date, collection_date)

    def retrieve(self) -> Any:
        if not self._address:
            self._address = self._find_address()
        s = self._session
        s.headers.update(HEADERS)
        r = s.get(
            "https://www.royalgreenwich.gov.uk/site/custom_scripts/apps/waste-collection/ajax-response-uprn.php",
            params={"address": self._address},
        )
        r.raise_for_status()
        if r.text == "ADDRESS_NOT_FOUND":
            raise SourceArgumentNotFound("address", self._address)
        data = r.json()
        collection_day_index = DAYS.index(data["Day"].upper()) + 1
        today = datetime.date.today()
        collection_date = today + datetime.timedelta(
            (collection_day_index - today.isoweekday()) % 7
        )
        black_top_date = self._get_black_top_bin_next_collection_date(
            data["Frequency"], collection_date
        )
        return r, black_top_date, self._get_bank_holiday_overrides()

    def parse(self, raw):
        response, black_top_date, bank_holiday_overrides = raw
        data = response.json()
        collection_day = data["Day"]
        today = datetime.date.today()
        collection_day_index = DAYS.index(collection_day.upper()) + 1
        this_week_collection_date = today + datetime.timedelta(
            (collection_day_index - today.isoweekday()) % 7
        )
        next_food_collection_date = black_top_date
        weeks_to_generate = 10
        recycling_collections = [
            {
                "date": self._correct_collection_date(
                    this_week_collection_date + datetime.timedelta(weeks=i),
                    bank_holiday_overrides,
                ),
                "type": "recycling",
            }
            for i in range(weeks_to_generate)
        ]
        garden_collections = [
            {
                "date": self._correct_collection_date(
                    this_week_collection_date + datetime.timedelta(weeks=i),
                    bank_holiday_overrides,
                ),
                "type": "garden",
            }
            for i in range(weeks_to_generate)
        ]
        food_collections = [
            {
                "date": self._correct_collection_date(
                    next_food_collection_date + datetime.timedelta(weeks=i * 2),
                    bank_holiday_overrides,
                ),
                "type": "food",
            }
            for i in range(int(weeks_to_generate / 2))
        ]
        return recycling_collections + garden_collections + food_collections


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
