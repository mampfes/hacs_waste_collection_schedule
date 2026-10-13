"""OloCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import logging
import re
from typing import Any

from curl_cffi import requests
from dateutil.rrule import WEEKLY, rrule, weekday

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
WASTE_TYPES = {
    "Zmiešaný odpad": "Zmesový komunálny odpad",
    "KBRO": "Kuchynský bioodpad",
    "BRO": "Záhradný bioodpad",
    "Plast": "Plast, kovy a nápojové kartóny",
    "Papier": "Papier",
    "Sklo": "Sklo",
}
GRAPHQL_URL = "https://olo-strapi.bratislava.sk/graphql"
GRAPHQL_QUERY = "\nquery PickupDaysByRegistrationNumber($registrationNumber: String!) {\n  pickupDays(filters: {registrationNumber: {eq: $registrationNumber}}) {\n    data {\n      attributes {\n        registrationNumber\n        address\n        frequency\n        wasteType\n        frequencySeason\n      }\n    }\n  }\n}\n"
MEILISEARCH_URL = (
    "https://olo-strapi-meilisearch.bratislava.sk/indexes/pickup-day/search"
)
API_KEY_REGEX = '"NEXT_PUBLIC_MEILISEARCH_HOST:",\\s*".*?",\\s*"(.*?)"'
API_KEY_SOURCE = "https://www.olo.sk/odpad/zistite-si-svoj-odvozovy-den"
API_KEY_JS_BASE = "https://www.olo.sk"
API_KEY_FALLBACK = "ae84ae0982c2162a81eb253765ceaa8593abd9105c71954cf5c9620b0178cbb6"


class _CalendarClient:
    _session: Any

    def __init__(self, street: str = "", registrationNumber: str = ""):
        self._street = street
        self._registrationNumber = registrationNumber

    def _find_api_key(self) -> str:
        """Find API key in the web page source code."""
        try:
            response = self._session.get(API_KEY_SOURCE, timeout=10)
            response.raise_for_status()
            page_text = response.text
            js_refs = re.findall('<script src="([^"]+)"', page_text)
            for js_ref in js_refs:
                api_key = self._parse_api_key(js_ref)
                if api_key:
                    return api_key
        except requests.RequestsError:
            pass
        return ""

    def _parse_api_key(self, js_ref: str) -> str:
        """Extract the API key from a .js file."""
        try:
            response = self._session.get(API_KEY_JS_BASE + js_ref, timeout=10)
            response.raise_for_status()
            js_source = response.text
            match = re.search(API_KEY_REGEX, js_source)
            if match:
                return match.group(1)
        except requests.RequestsError:
            pass
        return ""

    def _fetch_by_registration_number(self) -> list[dict[str, Any]]:
        """Fetch pickup days by registration number using GraphQL API."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        payload = {
            "query": GRAPHQL_QUERY,
            "variables": {"registrationNumber": self._registrationNumber},
            "operationName": "PickupDaysByRegistrationNumber",
        }
        response = self._session.post(
            GRAPHQL_URL, json=payload, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("data", {}).get("pickupDays", {}).get("data", [])
        return [item.get("attributes", {}) for item in items if item.get("attributes")]

    def _fetch_by_street(self) -> list[dict[str, Any]]:
        """Fetch pickup days by street name using MeiliSearch API."""
        api_key = self._find_api_key() or API_KEY_FALLBACK
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "authorization": f"Bearer {api_key}",
        }
        params = {
            "q": self._street,
            "limit": 100,
            "offset": 0,
            "filter": ['type = "pickup-day"'],
            "sort": ["pickup-day.address:asc"],
            "attributesToSearchOn": ["pickup-day.address"],
        }
        response = self._session.post(
            MEILISEARCH_URL, json=params, headers=headers, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("hits", [])
        return [item.get("pickup-day", {}) for item in items if item.get("pickup-day")]

    def _fetch_pickup_days(self) -> list[dict[str, Any]]:
        """Fetch pickup days using the appropriate API."""
        if self._registrationNumber:
            return self._fetch_by_registration_number()
        return self._fetch_by_street()

    def _is_date_in_season(
        self, date: datetime.date, season: tuple[tuple[int, int], tuple[int, int]]
    ) -> bool:
        """Check if a date falls within a season range."""
        (start_day, start_month), (end_day, end_month) = season
        year = date.year
        start_date = datetime.date(year, start_month, start_day)
        end_date = datetime.date(year, end_month, end_day)
        if end_date < start_date:
            return date >= start_date or date <= end_date
        return start_date <= date <= end_date

    def _parse_days(self, element: str) -> list[int]:
        """Parse a frequency element into a list of weekday numbers (1-7).

        Each element can be single ("4") or multi-digit ("135").
        """
        return [int(d) for d in element] if element.isdigit() else []

    def _generate_weekly_dates(
        self, elements: list[str], today: datetime.date, end_date: datetime.date
    ) -> list[datetime.date]:
        """Generate dates for a 4-week cycle pattern.

        Uses formula: (ISO_week - 1) % 4 == position
        - 2-element patterns are expanded to 4: [a,b] → [a,b,a,b]
        - Position 0,2 = odd weeks, Position 1,3 = even weeks
        """
        dates: list[datetime.date] = []
        for i, element in enumerate(elements):
            for day in self._parse_days(element):
                rule = rrule(
                    WEEKLY, dtstart=today, until=end_date, byweekday=weekday(day - 1)
                )
                dates.extend(
                    dt.date() for dt in rule if (dt.isocalendar()[1] - 1) % 4 == i
                )
        return dates

    def _generate_collection_dates(
        self, frequency: str, frequency_season: str | None
    ) -> list[datetime.date]:
        """
        Generate collection dates from OLO frequency string using a 4-week cycle.

        All patterns use formula: (ISO_week - 1) % 4 == position

        Frequency formats:
        - "[4,4]" - every week on Thursday (day 4)
        - "[-,4]" - even ISO weeks only on Thursday
        - "[4,-]" - odd ISO weeks only on Thursday
        - "[25,25]" - Tuesday (2) and Friday (5) every week
        - "[-,-,2,-]" - 4-week cycle: Tuesday in weeks where (week-1)%4 == 2
        - "[4,4];[5,5]" - seasonal patterns separated by semicolon

        Season format: "01/04-31/10, 01/11-31/03" (day/month ranges)
        """
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=90)
        seasons: list[tuple[tuple[int, int], tuple[int, int]]] = []
        if frequency_season:
            for part in frequency_season.split(","):
                part = part.strip()
                match = re.match("(\\d{2})/(\\d{2})-(\\d{2})/(\\d{2})", part)
                if match:
                    start_day, start_month, end_day, end_month = map(
                        int, match.groups()
                    )
                    seasons.append(((start_day, start_month), (end_day, end_month)))
                else:
                    _LOGGER.warning("Unrecognized season format: %s", part)
        dates: list[datetime.date] = []
        frequency_parts = frequency.split(";")
        for idx, part in enumerate(frequency_parts):
            part = part.strip()
            match = re.match("\\[([^\\]]+)\\]", part)
            if not match:
                _LOGGER.warning("Unrecognized frequency format: %s", part)
                continue
            content = match.group(1)
            elements = [e.strip() for e in content.split(",")]
            pattern_dates: list[datetime.date] = []
            if len(elements) == 2:
                elements = elements * 2
            if len(elements) == 4:
                pattern_dates.extend(
                    self._generate_weekly_dates(elements, today, end_date)
                )
            if seasons and idx < len(seasons):
                pattern_dates = [
                    d for d in pattern_dates if self._is_date_in_season(d, seasons[idx])
                ]
            dates.extend(pattern_dates)
        return sorted(dates)

    def retrieve(self) -> Any:
        if not self._street and (not self._registrationNumber):
            raise SourceArgumentExceptionMultiple(
                ["street", "registrationNumber"],
                "street or registrationNumber is required",
            )
        return self._fetch_pickup_days()

    def parse(self, pickup_days):
        if not pickup_days:
            raise SourceArgumentNotFound("street", self._street)
        entries: list[dict] = []
        seen: set[tuple[str, datetime.date]] = set()
        for item in pickup_days:
            waste_type = item.get("wasteType")
            if not waste_type:
                _LOGGER.warning("Missing wasteType in pickup day: %s", item)
                continue
            if waste_type in WASTE_TYPES:
                display_name = WASTE_TYPES[waste_type]
            else:
                display_name = waste_type
            frequency = item.get("frequency", "")
            frequency_season = item.get("frequencySeason")
            if not frequency:
                _LOGGER.warning("Missing frequency for waste type: %s", waste_type)
                continue
            dates = self._generate_collection_dates(frequency, frequency_season)
            for date in dates:
                key = (waste_type, date)
                if key not in seen:
                    seen.add(key)
                    entries.append({"date": date, "type": display_name})
        if not entries:
            raise ValueError("No waste collection dates found")
        return sorted(entries, key=lambda x: x["date"])


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
