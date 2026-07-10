#!/usr/bin/env python3

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Callable, ClassVar

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc
from waste_collection_schedule.waste_types import GENERAL_WASTE, ORGANIC, RECYCLABLES

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

    from .DeviceKeyStore import DeviceKeyStore


_device_key_store_method: Callable[[], DeviceKeyStore | None] | None = None


def get_device_key_store() -> DeviceKeyStore | None:
    """Lazy load the device key store method. So HA does not need to be loaded when running pytest."""
    global _device_key_store_method
    if _device_key_store_method is None:
        from .DeviceKeyStore import get_device_key_store as get_method

        _device_key_store_method = get_method
    return _device_key_store_method()


_LOGGER = logging.getLogger(__name__)

# WhatBinDay's raw bin-type codes are consistent across every known provider
# on the platform (WasteBin/RecycleBin/GreenBin), so the mapping to the
# canonical multilingual WasteType lives here once rather than being repeated
# (and re-worded) per source.
TYPE_VALUE_MAP = {
    "WasteBin": GENERAL_WASTE,
    "RecycleBin": RECYCLABLES,
    "GreenBin": ORGANIC,
}

# Address parts a source resolves before calling the retriever, either read
# directly from source.params (Kingston: separate street_number/street_name/
# suburb/post_code fields) or produced by a source-specific ``split_address``
# callable that parses one free-text address field (Lismore).
AddressParts = dict[str, str]

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_APP_PACKAGE = "com.socketsoftware.whatbinday.binston"


class WhatBinDayRetriever(RetrieverFunc):
    """Resolve an address to its collection events via the WhatBinDay API.

    WhatBinDay (whatbinday.com) is a white-label app platform: a client
    registers an anonymous "device", then submits an address (as a
    Google-Places-shaped payload) to get back the council's bin modules,
    including the ``CouncilBinModule`` with the raw ``CollectionEvents``.

    Handles the full round trip for a source:

    1. Resolve the address's individual parts (street number/name, suburb,
       postcode, state), either straight from ``source.params`` or via a
       source-supplied ``split_address`` callable that parses one free-text
       address field (Lismore's case; Kingston submits four separate fields).
    2. Optionally geocode the address via Nominatim (``geocode=True``) so the
       submitted coordinates resolve the applicable collection roster, which
       for some councils (e.g. Kingston) varies street-to-street and is keyed
       off the coordinates rather than the address text
       (see mampfes/hacs_waste_collection_schedule#6772).
    3. Register (or reuse a cached) device key. A key is cached first on the
       ``source`` instance (safe: one instance per configured address, reused
       across a running HA instance's periodic fetches) and, when the Home
       Assistant device-key Store is available, persisted there too so a
       restart does not re-register every configured address.
    4. POST the address to the services endpoint and return the raw
       ``CollectionEvents`` list from the ``CouncilBinModule`` response (``[]``
       when the address has no such module, so ``RAISE_ON_EMPTY`` surfaces a
       clear "address not found" error instead of a generic exception).

    Args are the ``source.params`` field names holding each address part (used
    when ``split_address`` is not given), plus:

    * ``split_address``: ``callable(raw_value) -> AddressParts`` that parses
      one free-text address field (named by ``address_field``) into
      ``street_number``/``street_name``/``suburb``/``post_code``/``state``.
      When given, the four `*_field` args are ignored.
    * ``state``: literal state used when ``split_address`` is not given (a
      source with separate address fields, like Kingston, does not also ask
      the user for their state).
    * ``geocode``: whether to resolve coordinates via Nominatim.
    * ``location_key``: a literal device-key-store key, or
      ``callable(AddressParts) -> str`` to derive one per address.
    """

    API_URLS: ClassVar = {
        "register_device": "https://api.whatbinday.com/V3/Device",
        "services": "https://api.whatbinday.com/V3/Device/{}/Services",
    }

    HEADERS: ClassVar = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(
        self,
        location_key: str | Callable[[AddressParts], str],
        street_number_field: str = "street_number",
        street_name_field: str = "street_name",
        suburb_field: str = "suburb",
        post_code_field: str = "post_code",
        state: str = "VIC",
        country: str = "Australia",
        app_package: str = DEFAULT_APP_PACKAGE,
        geocode: bool = False,
        split_address: Callable[[str], AddressParts] | None = None,
        address_field: str = "address",
    ):
        self.location_key = location_key
        self.street_number_field = street_number_field
        self.street_name_field = street_name_field
        self.suburb_field = suburb_field
        self.post_code_field = post_code_field
        self.state = state
        self.country = country
        self.app_package = app_package
        self.geocode = geocode
        self.split_address = split_address
        self.address_field = address_field

    def __call__(self, source: BaseSource) -> list[dict[str, Any]]:
        params = source.params
        if self.split_address is not None:
            parts = self.split_address(params[self.address_field])
        else:
            parts = {
                "street_number": str(params[self.street_number_field]),
                "street_name": str(params[self.street_name_field]),
                "suburb": str(params[self.suburb_field]),
                "post_code": str(params[self.post_code_field]),
                "state": self.state,
            }

        coordinates = None
        if self.geocode:
            coordinates = self._geocode(source, parts)

        location_key = (
            self.location_key(parts)
            if callable(self.location_key)
            else self.location_key
        )
        device_key = self._register_device(source, location_key)
        location_data = self._build_address_data(parts, coordinates)
        return self._fetch_services(source, device_key, location_data)

    def _geocode(self, source: BaseSource, parts: AddressParts) -> dict[str, float]:
        """Resolve the address to coordinates via Nominatim (OpenStreetMap)."""
        query = (
            f"{parts['street_number']} {parts['street_name']}, "
            f"{parts['suburb']} {parts['state']} {parts['post_code']}, Australia"
        )
        r = source.session.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": "1",
                "countrycodes": "au",
            },
            headers={"User-Agent": "hacs_waste_collection_schedule"},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise SourceArgumentNotFound("street_name", parts["street_name"])
        return {"lat": float(results[0]["lat"]), "lng": float(results[0]["lon"])}

    def _register_device(self, source: BaseSource, location_key: str) -> str:
        """Return a cached device key, or register a new one and cache it.

        Cached first on the ``source`` instance (one per configured address, so
        this is safe to reuse across that address's periodic fetches without
        leaking between different addresses that share this stateless,
        class-level retriever), then in the HA device-key Store when available
        so a restart does not re-register.
        """
        cached = getattr(source, "_whatbinday_device_key", None)
        if cached:
            return cached

        # get_device_key_store() lazily imports DeviceKeyStore, which imports
        # homeassistant: guard the whole lookup (not just the store call) so a
        # pytest/live-test run without homeassistant installed falls through
        # to a fresh registration instead of raising ModuleNotFoundError.
        store = None
        try:
            store = get_device_key_store()
            if store is not None:
                stored_key = store.get_device_key(location_key)
                if stored_key:
                    source._whatbinday_device_key = stored_key
                    return stored_key
        except Exception as e:
            _LOGGER.error(
                "Error accessing HA Store for location %s: %s", location_key, e
            )

        device_data = {
            "model": "SM-G973F",
            "manufacturer": "samsung",
            "api": "V3",
            "client": "2.1.8",
            "status": "Full Product",
            "pushID": "",
            "debug": False,
            "points": [],
            "suburbs": [],
            "regions": [],
            "os": "Android",
            "version": "31",
            "source": self.app_package,
        }
        r = source.session.post(
            self.API_URLS["register_device"],
            headers=self.HEADERS,
            json=device_data,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        response_shape.expect(
            bool(data.get("success")),
            source_name=response_shape.source_name(source),
            detail=f"device registration failed: {data.get('info', 'unknown error')}",
            raw=data,
        )
        device_key = data["data"]["key"]
        source._whatbinday_device_key = device_key

        if store is not None:
            try:
                store.set_device_key(location_key, device_key)
            except Exception as save_error:
                _LOGGER.error("Failed to save device key to HA Store: %s", save_error)

        return device_key

    def _build_address_data(
        self, parts: AddressParts, coordinates: dict[str, float] | None
    ) -> dict[str, Any]:
        """Build the Google-Places-shaped address payload the API expects."""
        street_number = parts["street_number"]
        street_name = parts["street_name"]
        suburb = parts["suburb"]
        post_code = parts["post_code"]
        state = parts["state"]

        formatted_address = (
            f"{street_number} {street_name}, {suburb} {state} {post_code}, "
            f"{self.country}"
        )
        address_components = [
            {
                "long_name": street_number,
                "short_name": street_number,
                "types": ["street_number"],
            },
            {
                "long_name": street_name,
                "short_name": street_name,
                "types": ["route"],
            },
            {
                "long_name": suburb,
                "short_name": suburb,
                "types": ["locality", "political"],
            },
            {
                "long_name": post_code,
                "short_name": post_code,
                "types": ["postal_code"],
            },
            {
                "long_name": state,
                "short_name": state,
                "types": ["administrative_area_level_1", "political"],
            },
            {
                "long_name": self.country,
                "short_name": "AU" if self.country == "Australia" else self.country,
                "types": ["country", "political"],
            },
        ]
        if coordinates is None:
            # Default coordinates for Victoria, Australia (matches the app's
            # own fallback; only reached for sources that don't geocode).
            coordinates = {"lat": -37.9759, "lng": 145.1350}
        return {
            "address_components": address_components,
            "formatted_address": formatted_address,
            "geometry": {"location": coordinates, "location_type": "APPROXIMATE"},
        }

    def _fetch_services(
        self, source: BaseSource, device_key: str, location_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        r = source.session.post(
            self.API_URLS["services"].format(device_key),
            headers=self.HEADERS,
            json=location_data,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        response_shape.expect(
            bool(data.get("success")),
            source_name=response_shape.source_name(source),
            detail=f"service lookup failed: {data.get('info', 'unknown error')}",
            raw=data,
        )

        bin_module = None
        for module in data.get("data", []):
            if module.get("ModuleName") == "CouncilBinModule":
                bin_module = module.get("Response")
                break

        if not bin_module:
            # No CouncilBinModule for this address: return no events rather
            # than raising here, so RAISE_ON_EMPTY reports a clear
            # SourceArgumentNotFound against the source's address field
            # instead of a generic exception.
            return []

        return bin_module.get("CollectionEvents", [])


class WhatBinDayParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the raw ``CollectionEvents`` list into ``(date, label)`` rows.

    Each event covers one date and lists every bin type collected that day in
    ``Items``; emits one row per (date, bin type) pair. Does no I/O, so it runs
    standalone against a cached ``CollectionEvents`` fixture.
    """

    def __call__(
        self,
        raw: list[dict[str, Any]],
        source: BaseSource | None = None,
    ) -> list[tuple[datetime.date, str]]:
        response_shape.expect(
            isinstance(raw, list),
            source_name=response_shape.source_name(source),
            detail="WhatBinDay response is not a list of collection events",
            raw=raw,
        )

        rows: list[tuple[datetime.date, str]] = []
        for event in raw:
            collection_date = datetime.datetime.strptime(
                event["Date"], "%Y-%m-%d"
            ).date()
            for bin_type in event.get("Items", []):
                rows.append((collection_date, bin_type))
        return rows
