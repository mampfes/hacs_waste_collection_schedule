"""Shared client for councils running the "OpenCities"/"MyArea" widget.

Many AU/NZ council websites expose the same two endpoints on their own
domain (the widget behind e.g. https://www.logan.qld.gov.au/MyLogan):

- ``GET <domain>/api/v1/myarea/search[fuzzy]`` — address search, returning
  JSON ``{"Items": [{"Id": "<geolocation-guid>", "AddressSingleLine": ...}]}``
  (a handful of legacy deployments return XML instead).
- ``GET <domain>/ocapi/Public/myarea/wasteservices`` — given a
  ``geolocationid``, returns ``{"success": bool, "responseContent": "<html>"}``
  where the HTML is a series of ``<article>``/``div.waste-services-result``
  blocks, each with an ``<h3>`` (waste type) and a ``.next-service`` element
  (next collection date).

This module centralises that flow behind :class:`OpenCitiesClient` so
per-council source files stay a thin ``OpenCitiesConfig`` + ``Source`` shim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_cffi_requests

from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)

DEFAULT_DATE_FORMAT = "%a %d/%m/%Y"


@dataclass(frozen=True)
class OpenCitiesConfig:
    """Per-council configuration for :class:`OpenCitiesClient`."""

    domain: str
    """Council base URL, e.g. ``"https://www.ballina.nsw.gov.au"`` (no trailing slash)."""

    argument_name: str = "address"
    """Exact ``Source.__init__`` kwarg name, used in raised exceptions."""

    search_fuzzy: bool = False
    """Use ``/api/v1/myarea/searchfuzzy`` instead of ``/api/v1/myarea/search``."""

    max_results: int | None = None
    """Optional ``maxresults`` query param on the search request."""

    search_response_format: Literal["json", "xml", "json_then_xml"] = "json"
    """Search response format. ``"json_then_xml"`` tries JSON, falls back to XML."""

    page_link: str | None = None
    """Optional ``pageLink`` query param required by some council instances."""

    ocsvclang: str = "en-AU"

    use_curl_cffi: bool = False
    """Use curl_cffi (Chrome impersonation) to bypass Akamai/Incapsula bot protection."""

    impersonate: str = "chrome"

    warm_up_url: str | None = None
    """A page fetched once, lazily, before the first API request (session/cookie priming)."""

    date_format: str = DEFAULT_DATE_FORMAT

    icon_keywords: dict[str, Any] | None = None
    """Lower-cased waste-type substring -> icon, checked in insertion order."""

    strip_type_suffixes: tuple[str, ...] = ()
    """Suffixes (case-insensitive) stripped from parsed waste-type labels, e.g. ``("collection",)``."""

    headers: dict[str, str] | None = None

    timeout: int = 30

    strict_address_matching: bool = True
    """
    If True (default), multiple search results are disambiguated by exact
    (case/space-insensitive) match against ``AddressSingleLine``, raising
    ``SourceArgAmbiguousWithSuggestions`` when that's not conclusive. Set to
    False only for legacy XML search responses that carry no address text at
    all, where the first result is the only option.
    """


class OpenCitiesClient:
    def __init__(self, config: OpenCitiesConfig) -> None:
        self._cfg = config
        self._session = self._build_session()
        self._geolocation_id: str | None = None
        self._warmed_up = False

    # ---- public API ---------------------------------------------------

    def fetch(
        self, address: str | None = None, geolocation_id: str | None = None
    ) -> list[Collection]:
        """Resolve collections for an address, or directly for a geolocation id.

        When resolving from ``address``, the geolocation id is cached across
        calls (HA polls ``fetch()`` repeatedly) so only the first call pays
        for the address search. If a cached id later fails, it is re-resolved
        once and the wasteservices call retried.
        """
        if geolocation_id is not None:
            return self.fetch_by_geolocation_id(geolocation_id)

        if address is None:
            raise ValueError("Either address or geolocation_id must be provided")

        used_cache = self._geolocation_id is not None
        if not used_cache:
            self._geolocation_id = self.resolve_geolocation_id(address)

        try:
            return self.fetch_by_geolocation_id(self._geolocation_id)  # type: ignore[arg-type]
        except SourceArgumentNotFound:
            if not used_cache:
                raise
            self._geolocation_id = self.resolve_geolocation_id(address)
            return self.fetch_by_geolocation_id(self._geolocation_id)

    def resolve_geolocation_id(self, address: str) -> str:
        self._ensure_warmed_up()
        items = self._search(address)
        return self._select_address(address, items)

    def fetch_by_geolocation_id(self, geolocation_id: str) -> list[Collection]:
        self._ensure_warmed_up()
        params: dict[str, str] = {
            "geolocationid": geolocation_id,
            "ocsvclang": self._cfg.ocsvclang,
        }
        if self._cfg.page_link:
            params["pageLink"] = self._cfg.page_link
        response = self._get(
            f"{self._cfg.domain}/ocapi/Public/myarea/wasteservices", params
        )
        data = response.json()
        if not data.get("success", True) or not data.get("responseContent"):
            raise SourceArgumentNotFound(self._cfg.argument_name, geolocation_id)
        return self._parse_wasteservices_html(data["responseContent"])

    # ---- internals ------------------------------------------------------

    def _build_session(self):
        if self._cfg.use_curl_cffi:
            session = curl_cffi_requests.Session(impersonate=self._cfg.impersonate)
        else:
            session = requests.Session()
        if self._cfg.headers:
            session.headers.update(self._cfg.headers)
        return session

    def _get(self, url: str, params: dict[str, Any] | None = None):
        response = self._session.get(url, params=params, timeout=self._cfg.timeout)
        response.raise_for_status()
        return response

    def _ensure_warmed_up(self) -> None:
        if self._warmed_up or not self._cfg.warm_up_url:
            return
        self._get(self._cfg.warm_up_url)
        self._warmed_up = True

    def _search(self, address: str) -> list[dict[str, Any]]:
        path = "searchfuzzy" if self._cfg.search_fuzzy else "search"
        params: dict[str, Any] = {"keywords": address}
        if self._cfg.max_results is not None:
            params["maxresults"] = self._cfg.max_results
        response = self._get(f"{self._cfg.domain}/api/v1/myarea/{path}", params)

        fmt = self._cfg.search_response_format
        if fmt == "xml":
            return self._parse_search_xml(response.text)
        if fmt == "json_then_xml":
            try:
                return response.json().get("Items") or []
            except ValueError:
                return self._parse_search_xml(response.text)
        return response.json().get("Items") or []

    @staticmethod
    def _parse_search_xml(text: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(text, "xml")
        items: list[dict[str, Any]] = []
        for result in soup.find_all("PhysicalAddressSearchResult"):
            id_el = result.find("Id")
            if id_el and id_el.text.strip():
                item: dict[str, Any] = {"Id": id_el.text.strip()}
                address_el = result.find("AddressSingleLine")
                if address_el and address_el.text.strip():
                    item["AddressSingleLine"] = address_el.text.strip()
                items.append(item)
        return items

    def _select_address(self, address: str, items: list[dict[str, Any]]) -> str:
        if not items:
            raise SourceArgumentNotFound(self._cfg.argument_name, address)
        if len(items) == 1 or not self._cfg.strict_address_matching:
            return items[0]["Id"]

        normalized = address.lower().replace(" ", "")
        exact = [
            item
            for item in items
            if item.get("AddressSingleLine", "").lower().replace(" ", "") == normalized
        ]
        if len(exact) == 1:
            return exact[0]["Id"]

        if not any(item.get("AddressSingleLine") for item in items):
            # No address text to disambiguate with (e.g. legacy XML results) —
            # fall back to the first match rather than crash.
            return items[0]["Id"]

        suggestions = [item.get("AddressSingleLine", item["Id"]) for item in items]
        raise SourceArgAmbiguousWithSuggestions(
            self._cfg.argument_name, address, suggestions
        )

    def _parse_wasteservices_html(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []
        for block in soup.select("article, div.waste-services-result"):
            title = block.select_one("h3")
            next_service = block.select_one(".next-service")
            if title is None or next_service is None:
                continue

            waste_type = title.get_text(" ", strip=True)
            for suffix in self._cfg.strip_type_suffixes:
                if waste_type.lower().endswith(suffix.lower()):
                    waste_type = waste_type[: -len(suffix)].strip()

            date_text = next_service.get_text(" ", strip=True)
            if not date_text:
                continue
            collection_date = self._parse_date(date_text)
            if collection_date is None:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=self._resolve_icon(waste_type),
                )
            )
        return entries

    def _parse_date(self, text: str) -> date | None:
        try:
            return datetime.strptime(text, self._cfg.date_format).date()
        except ValueError:
            return None

    def _resolve_icon(self, label: str) -> Any | None:
        if not self._cfg.icon_keywords:
            return None
        lowered = label.lower()
        for keyword, icon in self._cfg.icon_keywords.items():
            if keyword.lower() in lowered:
                return icon
        return None
