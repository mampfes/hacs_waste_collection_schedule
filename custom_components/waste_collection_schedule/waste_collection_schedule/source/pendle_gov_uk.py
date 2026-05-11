import datetime
import logging
import re
from typing import Any, Optional

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Pendle Borough Council"
DESCRIPTION = "Source for Pendle Borough Council."
URL = "https://www.pendle.gov.uk/binday"
TEST_CASES = {
    "Pendle Market Street": {
        "postcode": "BB9 7LJ",
        "address": "PENDLE LEISURE TRUST, 1, MARKET STREET, NELSON",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter the postcode and address as returned by Pendle Borough Council. "
        "Set garden_waste_bin to true when the property has a green garden waste "
        "bin, and set collection_zone only if Pendle returns multiple schedules "
        "for the address."
    )
}
PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Address as returned by Pendle Borough Council.",
        "collection_zone": (
            "Collection zone, only needed if Pendle returns multiple schedules "
            "for your address."
        ),
        "future_collection_dates": "Generate future collection dates.",
        "garden_waste_bin": (
            "Set to true when the property has a green garden waste bin collected "
            "with the blue and brown bins."
        ),
        "postcode": "Postcode for the property.",
    }
}
PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address": "Address",
        "collection_zone": "Collection Zone",
        "future_collection_dates": "Include Future Collection Dates",
        "garden_waste_bin": "Has Garden Waste Bin",
    }
}

ICON_MAP = {
    "blue collection": "mdi:recycle",
    "brown collection": "mdi:leaf",
    "food collection": "mdi:food-apple",
    "food waste collection": "mdi:food-apple",
    "green collection": "mdi:leaf",
    "grey collection": "mdi:trash-can",
}

MAP_CONFIG_URL = "https://opus4.co.uk/api/v1/map-configs/{map_id}"
ADDRESS_SEARCH_URL = "https://opus4.co.uk/api/v1/address-search"
DEFAULT_CLIENT = "pendle"
DEFAULT_CLIENT_ID = 5
DEFAULT_MAP_ID = 3606
DEFAULT_LANGUAGE = "en-GB"
DEFAULT_WEEKS_AHEAD = 12
_LOGGER = logging.getLogger(__name__)
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) " "Gecko/20100101 Firefox/128.0"
    )
}
WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


class Source:
    def __init__(
        self,
        postcode: str,
        address: str,
        collection_zone: Optional[str] = None,
        garden_waste_bin: bool = False,
        future_collection_dates: bool = False,
    ):
        if not postcode:
            raise SourceArgumentRequired(
                "postcode", "it is needed to look up Pendle addresses"
            )
        if not address:
            raise SourceArgumentRequired(
                "address", "it is needed to pick the correct Pendle property"
            )

        self._postcode = postcode
        self._address = address
        self._collection_zone = (
            str(collection_zone).strip() if collection_zone else None
        )
        self._garden_waste_bin = garden_waste_bin
        self._future_collection_dates = future_collection_dates
        self._session = requests.Session()
        self._session.headers.update(REQUEST_HEADERS)

    @staticmethod
    def _normalize(value: Optional[str]) -> str:
        if value is None:
            return ""
        return re.sub(r"[^A-Za-z0-9]", "", value).upper()

    @staticmethod
    def _parse_relative_date(value: Optional[str]) -> Optional[datetime.date]:
        if not value:
            return None

        today = datetime.date.today()
        text = value.strip().lower()

        match = re.search(r"\(in (\d+) days?\)", text)
        if match:
            return today + datetime.timedelta(days=int(match.group(1)))

        match = re.search(r"\bin (\d+) days?\b", text)
        if match:
            return today + datetime.timedelta(days=int(match.group(1)))

        match = re.search(
            r"\bin (\d+) weeks?\s+on\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            text,
        )
        if match:
            weeks = int(match.group(1))
            target = WEEKDAYS[match.group(2)]
            days_ahead = (target - today.weekday()) % 7
            return today + datetime.timedelta(days=days_ahead, weeks=weeks)

        match = re.search(r"\bin (\d+) weeks?\b", text)
        if match:
            return today + datetime.timedelta(weeks=int(match.group(1)))

        if text == "today":
            return today
        if text == "tomorrow":
            return today + datetime.timedelta(days=1)

        match = re.search(
            r"\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            text,
        )
        if match:
            target = WEEKDAYS[match.group(1)]
            days_ahead = (target - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return today + datetime.timedelta(days=days_ahead)

        return None

    @staticmethod
    def _parse_start_date(value: Optional[str]) -> Optional[datetime.date]:
        if not value:
            return None
        try:
            return datetime.datetime.strptime(value.strip(), "%d %B, %Y").date()
        except ValueError:
            return None

    @staticmethod
    def _next_occurrence_from_anchor(
        start_date: Optional[datetime.date], frequency_weeks: Optional[int]
    ) -> Optional[datetime.date]:
        if start_date is None:
            return None

        if not frequency_weeks or frequency_weeks < 1:
            return start_date

        today = datetime.date.today()
        next_date = start_date
        while next_date < today:
            next_date += datetime.timedelta(weeks=frequency_weeks)
        return next_date

    @staticmethod
    def _parse_weekday(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        return WEEKDAYS.get(value.strip().lower())

    def _resolve_next_collection_date(
        self, item: dict[str, Any], title: str, frequency_weeks: Optional[int]
    ) -> Optional[datetime.date]:
        expected_date = self._next_occurrence_from_anchor(
            self._parse_start_date(item.get("startDate")),
            frequency_weeks,
        )
        actual_date = self._parse_relative_date(item.get("when"))
        weekday = self._parse_weekday(item.get("day"))

        if (
            actual_date is not None
            and weekday is not None
            and actual_date.weekday() != weekday
        ):
            _LOGGER.warning(
                "Pendle parsed when mismatch for %s: parsed %s but council day is %s. "
                "Ignoring parsed date and falling back to schedule anchor.",
                title,
                actual_date.isoformat(),
                item.get("day"),
            )
            actual_date = None

        next_date = actual_date or expected_date
        if next_date is None:
            return None

        if (
            actual_date is not None
            and expected_date is not None
            and actual_date != expected_date
        ):
            _LOGGER.warning(
                "Pendle schedule override for %s: expected %s from startDate/frequency, "
                "but council when says %s. Using council date.",
                title,
                expected_date.isoformat(),
                actual_date.isoformat(),
            )

        if weekday is not None and next_date.weekday() != weekday:
            _LOGGER.warning(
                "Pendle weekday mismatch for %s: resolved %s but council day is %s.",
                title,
                next_date.isoformat(),
                item.get("day"),
            )

        return next_date

    @staticmethod
    def _get_icon(title: str) -> Optional[str]:
        key = title.strip().lower()
        return ICON_MAP.get(key)

    def _expand_optional_collections(self, title: str) -> list[str]:
        titles = [title]
        normalized = title.strip().lower()
        if self._garden_waste_bin and normalized in {
            "blue collection",
            "brown collection",
        }:
            titles.append("Green Collection")
        return titles

    @staticmethod
    def _expand_dates(
        first_date: datetime.date, frequency_weeks: Optional[int]
    ) -> list[datetime.date]:
        if not frequency_weeks or frequency_weeks < 1:
            return [first_date]

        dates = [first_date]
        next_date = first_date
        while True:
            next_date = next_date + datetime.timedelta(weeks=frequency_weeks)
            if (next_date - first_date).days > DEFAULT_WEEKS_AHEAD * 7:
                break
            dates.append(next_date)
        return dates

    def _get_map_config(self) -> dict[str, Any]:
        response = self._session.get(
            MAP_CONFIG_URL.format(map_id=DEFAULT_MAP_ID),
            params={"c": DEFAULT_CLIENT_ID, "l": DEFAULT_LANGUAGE},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _lookup_addresses(self) -> list[dict[str, Any]]:
        response = self._session.get(
            ADDRESS_SEARCH_URL,
            params={
                "address": self._address,
                "postcode": self._postcode,
                "page": 1,
                "size": 25,
                "client": DEFAULT_CLIENT,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()

        addresses = payload.get("Results", {}).get("Addresses", {}).get("Address")
        if addresses is None:
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "Pendle did not return any matching addresses",
            )

        if isinstance(addresses, dict):
            return [addresses]
        return list(addresses)

    def _select_address(self, addresses: list[dict[str, Any]]) -> dict[str, Any]:
        expected = self._normalize(self._address)
        exact = [
            item
            for item in addresses
            if self._normalize(item.get("FullAddress")) == expected
        ]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._address,
                [item.get("FullAddress") for item in exact],
            )

        matches = [
            item
            for item in addresses
            if expected in self._normalize(item.get("FullAddress"))
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "address",
                self._address,
                [item.get("FullAddress") for item in matches],
            )

        raise SourceArgumentNotFound(
            "address",
            self._address,
            "no Pendle address matched that text within the postcode",
        )

    def _select_zone(self, collections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        locations = sorted(
            {
                str(item.get("location")).strip()
                for item in collections
                if item.get("location") is not None
                and str(item.get("location")).strip()
            }
        )
        if len(locations) <= 1:
            return collections

        if self._collection_zone:
            selected = [
                item
                for item in collections
                if str(item.get("location", "")).strip() == self._collection_zone
            ]
            if selected:
                return selected
            raise SourceArgumentNotFound(
                "collection_zone",
                self._collection_zone,
                "Pendle did not return that collection zone for the selected address",
            )

        raise SourceArgAmbiguousWithSuggestions(
            "collection_zone",
            "multiple Pendle collection zones were returned for this address",
            locations,
        )

    def _fetch_collections(
        self, x: float, y: float, wms_url: str, layer_id: str
    ) -> list[dict[str, Any]]:
        for buffer_size in (500, 1000, 1500):
            response = self._session.get(
                wms_url,
                params={
                    "service": "WMS",
                    "version": "1.1.1",
                    "request": "GetFeatureInfo",
                    "layers": "none",
                    "styles": "",
                    "srs": "EPSG:27700",
                    "bbox": f"{x-buffer_size},{y-buffer_size},{x+buffer_size},{y+buffer_size}",
                    "width": 101,
                    "height": 101,
                    "query_layers": layer_id,
                    "info_format": "application/json",
                    "x": 50,
                    "y": 50,
                    "feature_count": 10,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return list(data)

        return []

    def fetch(self) -> list[Collection]:
        map_config = self._get_map_config()
        addresses = self._lookup_addresses()
        selected_address = self._select_address(addresses)

        layer_groups = map_config.get("legend", {}).get("layerGroups", [])
        layers = layer_groups[0].get("layers", []) if layer_groups else []
        layer_id = layers[0].get("id") if layers else None
        wms_url = map_config.get("doubleClick", {}).get("url")

        if not layer_id or not wms_url:
            raise SourceArgumentException(
                "address", "Pendle map configuration is missing the query layer details"
            )

        collections = self._fetch_collections(
            float(selected_address["X"]),
            float(selected_address["Y"]),
            wms_url,
            layer_id,
        )
        collections = self._select_zone(collections)

        if not collections:
            raise SourceArgumentNotFound("address", self._address)

        entries: list[Collection] = []
        for item in collections:
            title = item.get("title", "Collection")
            frequency_weeks = item.get("frequency")
            next_date = self._resolve_next_collection_date(
                item,
                title,
                frequency_weeks,
            )
            if next_date is None:
                continue

            if self._future_collection_dates:
                collection_dates = self._expand_dates(next_date, frequency_weeks)
            else:
                collection_dates = [next_date]
            for collection_date in collection_dates:
                for expanded_title in self._expand_optional_collections(title):
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=expanded_title,
                            icon=self._get_icon(expanded_title),
                        )
                    )

        entries.sort(key=lambda item: (item.date, item.type))
        return entries
