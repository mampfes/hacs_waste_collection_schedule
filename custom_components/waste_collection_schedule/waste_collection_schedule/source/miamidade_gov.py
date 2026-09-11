import re
from datetime import date, timedelta
from typing import Any

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

from ..service.ArcGis import ArcGisError, ArcGisQueryError, geocode, query_feature_layer

TITLE = "Miami-Dade County"
DESCRIPTION = "Source for Miami-Dade County garbage and recycling pickup."
URL = "https://www.miamidade.gov/global/solidwaste/home.page"
COUNTRY = "us"
SOURCE_CODEOWNERS = ["@barrelcollector"]

TEST_CASES = {
    "Route codes": {
        "garbage_route": "5206",
        "recycling_route": "32A385",
    },
}

GARBAGE_LAYER_URL = (
    "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
    "GarbagePickupRoute_gdb/FeatureServer/0"
)
RECYCLING_LAYER_URL = (
    "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
    "RecyclingRoute_gdb/FeatureServer/0"
)
GEOCODER_URL = (
    "https://giswspro.miamidade.gov/arcgis/rest/services/"
    "MDC_Locators/MD_LocatorCityName/GeocodeServer"
)
WEBMAP_DATA_URL = (
    "https://www.arcgis.com/sharing/rest/content/items/"
    "2e6d2b7bcc854e1e89d953c439ffd917/data"
)

WEEKS_AHEAD = 26
RECYCLE_PICKUP_EXPRESSION_TITLE = "Recycle Pick up Days"

ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use either address, or route codes from Miami-Dade's official Garbage "
        "and Recycling Pickup Days lookup: "
        "https://gisweb.miamidade.gov/garbageandrecyclingpickupdays/"
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Miami-Dade service address. Optional if route codes are provided.",
        "garbage_route": "Garbage route code. Optional if address is provided.",
        "recycling_route": "Recycling route code. Optional if address is provided.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
        "garbage_route": "Garbage Route",
        "recycling_route": "Recycling Route",
    },
}


class Source:
    def __init__(
        self,
        address: str | None = None,
        garbage_route: str | None = None,
        recycling_route: str | None = None,
    ):
        self._address = address.strip() if address else None
        self._garbage_route = garbage_route.strip() if garbage_route else None
        self._recycling_route = (
            recycling_route.strip().upper() if recycling_route else None
        )
        self._session = requests.Session()

    def fetch(self) -> list[Collection]:
        if not any([self._address, self._garbage_route, self._recycling_route]):
            raise SourceArgumentRequired(
                "address",
                "Provide an address or at least one Miami-Dade route code.",
            )

        if self._address:
            garbage_attrs, recycling_attrs = self._routes_by_address(self._address)
        else:
            garbage_attrs = (
                self._garbage_by_route(self._garbage_route)
                if self._garbage_route
                else None
            )
            recycling_attrs = (
                self._recycling_by_route(self._recycling_route)
                if self._recycling_route
                else None
            )

        entries: list[Collection] = []
        if garbage_attrs:
            entries.extend(self._garbage_collections(garbage_attrs))
        if recycling_attrs:
            entries.extend(self._recycling_collections(recycling_attrs))

        if not entries:
            raise SourceArgumentNotFound("address", self._address or "route codes")

        return sorted(entries, key=lambda entry: entry.date)

    def _routes_by_address(
        self, address: str
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        try:
            location = geocode(address, geocode_url=GEOCODER_URL)
        except ArcGisError as e:
            raise SourceArgumentNotFound("address", address) from e

        garbage_attrs = self._first_spatial_match(GARBAGE_LAYER_URL, location)
        recycling_attrs = self._first_spatial_match(RECYCLING_LAYER_URL, location)
        if not garbage_attrs and not recycling_attrs:
            raise SourceArgumentNotFound("address", address)
        return garbage_attrs, recycling_attrs

    @staticmethod
    def _first_spatial_match(
        layer_url: str, location: dict[str, float]
    ) -> dict[str, Any] | None:
        try:
            features = query_feature_layer(layer_url, geometry=location)
        except ArcGisQueryError:
            return None
        return features[0] if features else None

    @staticmethod
    def _garbage_by_route(route: str | None) -> dict[str, Any]:
        try:
            features = query_feature_layer(
                GARBAGE_LAYER_URL,
                where=f"ALIASID='{_arcgis_quote(route or '')}'",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("garbage_route", route or "") from e
        return features[0]

    @staticmethod
    def _recycling_by_route(route: str | None) -> dict[str, Any]:
        try:
            features = query_feature_layer(
                RECYCLING_LAYER_URL,
                where=f"ROUTE='{_arcgis_quote(route or '')}'",
            )
        except ArcGisError as e:
            raise SourceArgumentNotFound("recycling_route", route or "") from e
        return features[0]

    @staticmethod
    def _garbage_collections(attrs: dict[str, Any]) -> list[Collection]:
        entries: list[Collection] = []
        for weekday in _split_weekdays(str(attrs.get("WEEKDAYS") or "")):
            entries.extend(_weekly_collections(weekday, "Garbage"))
        return entries

    def _recycling_collections(self, attrs: dict[str, Any]) -> list[Collection]:
        route = str(attrs.get("PICKUPWEEK") or "").upper()
        route_day = str(attrs.get("DAYID") or "")
        expression = self._recycling_expression()
        base_dates = self._recycling_base_dates(expression)
        holiday_delay = _recycling_holiday_delay(expression)
        base_date = base_dates.get((route, route_day))
        if base_date is None:
            raise SourceArgumentNotFound("recycling_route", str(attrs.get("ROUTE")))

        cycle_length = 7 if route == "C" else 14
        today = date.today()
        current = _first_cycle_date_on_or_after(base_date, cycle_length, today)
        entries = []
        for _ in range(WEEKS_AHEAD if route == "C" else WEEKS_AHEAD // 2):
            collection_date = _apply_holiday_delay(current, holiday_delay)
            entries.append(
                Collection(
                    date=collection_date,
                    t="Recycling",
                    icon=ICON_MAP["Recycling"],
                )
            )
            current += timedelta(days=cycle_length)
        return entries

    @staticmethod
    def _recycling_base_dates(expression: str) -> dict[tuple[str, str], date]:
        base_dates: dict[tuple[str, str], date] = {}
        current_route = None
        current_route_day = None

        for line in expression.splitlines():
            route_match = re.search(r'route == "([ABC])"', line)
            if route_match:
                current_route = route_match.group(1)
                continue

            route_day_match = re.search(r'routeDay == "([1-5])"', line)
            if route_day_match:
                current_route_day = route_day_match.group(1)
                continue

            date_match = re.search(r"Date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)", line)
            if current_route and current_route_day and date_match:
                year, arcade_month, day = date_match.groups()
                base_dates[(current_route, current_route_day)] = date(
                    int(year),
                    int(arcade_month) + 1,
                    int(day),
                )
                current_route_day = None

        if not base_dates:
            raise ValueError("Could not parse Miami-Dade recycling pickup expression")
        return base_dates

    def _recycling_expression(self) -> str:
        response = self._session.get(
            WEBMAP_DATA_URL,
            params={"f": "json"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        expression = _find_expression(data, RECYCLE_PICKUP_EXPRESSION_TITLE)
        if expression is None:
            raise ValueError("Could not find Miami-Dade recycling pickup expression")
        return expression


def _find_expression(value: Any, title: str) -> str | None:
    if isinstance(value, dict):
        if value.get("title") == title and isinstance(value.get("expression"), str):
            return value["expression"]
        for child in value.values():
            expression = _find_expression(child, title)
            if expression is not None:
                return expression
    elif isinstance(value, list):
        for child in value:
            expression = _find_expression(child, title)
            if expression is not None:
                return expression
    return None


def _weekly_collections(weekday: str, waste_type: str) -> list[Collection]:
    weekday_index = WEEKDAYS.get(weekday)
    if weekday_index is None:
        return []
    today = date.today()
    days_ahead = (weekday_index - today.weekday()) % 7
    next_date = today + timedelta(days=days_ahead)
    return [
        Collection(
            date=next_date + timedelta(weeks=i),
            t=waste_type,
            icon=ICON_MAP[waste_type],
        )
        for i in range(WEEKS_AHEAD)
    ]


def _split_weekdays(value: str) -> list[str]:
    return [day.title() for day in value.replace(",", " ").split() if day]


def _recycling_holiday_delay(expression: str) -> tuple[int, int, int] | None:
    holiday_match = re.search(
        r"pickupMonth\s*==\s*(\d+)\s*&&\s*pickupDay\s*==\s*(\d+)",
        expression,
    )
    delay_match = re.search(
        r"DateAdd\(nextPickupDate,\s*(\d+),\s*\"days\"\)",
        expression,
    )
    if not holiday_match or not delay_match:
        return None

    arcade_month, day = holiday_match.groups()
    return int(arcade_month) + 1, int(day), int(delay_match.group(1))


def _apply_holiday_delay(
    collection_date: date, holiday_delay: tuple[int, int, int] | None
) -> date:
    if holiday_delay is None:
        return collection_date

    month, day, delay_days = holiday_delay
    if collection_date.month == month and collection_date.day == day:
        return collection_date + timedelta(days=delay_days)
    return collection_date


def _first_cycle_date_on_or_after(
    base_date: date, cycle_length: int, target: date
) -> date:
    days_since = (target - base_date).days
    cycles = days_since // cycle_length
    candidate = base_date + timedelta(days=cycles * cycle_length)
    if candidate < target:
        candidate += timedelta(days=cycle_length)
    return candidate


def _arcgis_quote(value: str) -> str:
    return value.strip().replace("'", "''").upper()
