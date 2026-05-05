"""
IntraMaps API Client Library.

This module provides a structured, production-ready interface for interacting
with IntraMaps GIS web services. It handles the multi-step handshake required
to resolve physical addresses into internal database keys and map selections.

Typical workflow:
    1. Initialize IntraMapsClientConfig with base URL and Project ID.
    2. Create an IntraMapsClient instance (preferably using a context manager).
    3. Call select_address() to perform the search and selection in one step.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Custom Exception Hierarchy ---


class IntraMapsError(Exception):
    """Base exception class for all IntraMaps-related failures."""

    pass


class IntraMapsSessionError(IntraMapsError):
    """Raised when the client fails to establish or maintain a session token."""

    pass


class IntraMapsSearchError(IntraMapsError):
    """Raised when an address lookup fails or returns zero matches."""

    pass


# --- Configuration ---


@dataclass(frozen=True)
class MapsClientConfig:
    """
    Configuration schema for the IntraMaps Client.

    Attributes:
        base_url: The root URL of the IntraMaps server (e.g., https://maps.example.gov).
        instance: The software instance version/path (default: "IntraMaps23A").
        project: The UUID of the specific map project.
        config_id: The configuration UUID (often remains 0s).
        app_type: The IntraMaps application module (default: "MapBuilder").
        default_selection_layer: Fallback layer ID if the search result doesn't provide one.
        default_map_key: Fallback map key if the search result doesn't provide one.
        timeout_s: Request timeout in seconds.
        retries: Number of automatic retries for transient 5xx errors.
    """

    base_url: str
    instance: str = "IntraMaps23A"
    project: str = "1917ad36-6a1d-4145-9eeb-736f8fa9646d"
    config_id: str = "00000000-0000-0000-0000-000000000000"
    app_type: str = "MapBuilder"
    dataset_code: str = ""
    include_disabled_modules: bool = True

    # Lite config support (required by some SaaS-hosted instances)
    lite_config_id: str = ""

    # Override to select a specific module instead of auto-discovering
    module_id: str = ""

    # Selection layer filter for search queries
    selection_layer_filter: str = ""

    # Defaults for selection logic
    default_selection_layer: str = "9f256a90-46da-4519-9d0e-d3d1b4e8c462"
    default_map_key: str = "11865430"

    # Connection management
    timeout_s: int = 25
    retries: int = 3
    user_agent: str = "IntraMapsClient/2.0 (Production)"


# --- Client ---


class MapsClient:
    """
    A stateful client for the IntraMaps API.

    This client manages the 'X-IntraMaps-Session' token, discovers form metadata
    automatically, and provides high-level methods for address resolution.
    """

    def __init__(self, config: MapsClientConfig):
        """Initialize the client with a specific configuration and session pool."""
        self.cfg = config
        self.log = logging.getLogger(__name__)
        self._session = self._build_session()

        # Cached state to avoid redundant API calls
        self.intramaps_session: str | None = None
        self._module_id: str | None = None
        self._address_form_template_id: str | None = None

    def _build_session(self) -> requests.Session:
        """
        Configure the underlying requests Session with retry logic and standard headers.

        Returns:
            A configured requests.Session object.
        """
        session = requests.Session()

        # Define retry behavior for flaky network conditions or server overload
        retry_strategy = Retry(
            total=self.cfg.retries,
            backoff_factor=1,  # Exponential backoff (1s, 2s, 4s...)
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set persistent headers required by the IntraMaps Web API
        session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "User-Agent": self.cfg.user_agent,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.cfg.base_url.rstrip("/"),
                "Referer": f"{self.cfg.base_url.rstrip('/')}/",
            }
        )
        return session

    def _url(self, path: str) -> str:
        """Build a full URL including the instance version."""
        base = self.cfg.base_url.rstrip("/")
        return f"{base}/{self.cfg.instance}{path}"

    def ensure_session(self, force: bool = False) -> str:
        """
        Handshakes with the Projects endpoint to get a Session Token.

        This is the first step in the IntraMaps lifecycle. It also extracts the
        primary Module ID needed for subsequent form lookups.

        Args:
            force: If True, ignores cached session and requests a new one.

        Returns:
            The session token string.
        """
        if self.intramaps_session and self._module_id and not force:
            return self.intramaps_session

        self.log.debug("Initializing new IntraMaps session...")

        params = {
            "configId": self.cfg.config_id,
            "appType": self.cfg.app_type,
            "project": self.cfg.project,
            "datasetCode": self.cfg.dataset_code,
            "includeDisabledModules": str(self.cfg.include_disabled_modules).lower(),
        }
        if self.cfg.lite_config_id:
            params["liteConfigId"] = self.cfg.lite_config_id

        try:
            r = self._session.post(
                self._url("/ApplicationEngine/Projects/"),
                params=params,
                timeout=self.cfg.timeout_s,
            )
            r.raise_for_status()

            # Extract token from headers; IntraMaps uses this instead of standard cookies
            ims = r.headers.get("X-IntraMaps-Session")
            if not ims:
                raise IntraMapsSessionError(
                    "Response missing 'X-IntraMaps-Session' header."
                )

            self.intramaps_session = ims.strip()

            # Use configured module_id if provided, otherwise discover from project
            if self.cfg.module_id:
                self._module_id = self.cfg.module_id
            else:
                data = r.json()
                modules = data.get("moduleList") or data.get("modules") or []
                if not modules or not isinstance(modules, list):
                    raise IntraMapsSessionError(
                        "No modules found in project configuration."
                    )

                self._module_id = modules[0].get("id")
                if not self._module_id:
                    raise IntraMapsSessionError(
                        "Module list found but first module has no ID."
                    )

            return self.intramaps_session

        except requests.RequestException as e:
            raise IntraMapsSessionError(f"Failed to connect to IntraMaps: {e}")

    def _get_form_template_id(self) -> str:
        """
        Discovers the specific 'FullText' search form ID from the module config.

        IntraMaps requires a specific 'TemplateId' for address searches, which
        can vary by project. This method crawls the forms list to find the best match.
        """
        if self._address_form_template_id:
            return self._address_form_template_id

        self.ensure_session()

        url = self._url("/ApplicationEngine/Modules/")
        params = {"IntraMapsSession": self.intramaps_session}
        payload = {
            "module": self._module_id,
            "includeWktInSelection": True,
            "includeBasemaps": False,
        }

        r = self._session.post(
            url, params=params, json=payload, timeout=self.cfg.timeout_s
        )
        r.raise_for_status()

        forms = r.json().get("forms", [])

        # Logic: Find a form named 'Address' with subtype 'FullText'.
        # Fall back to any 'FullText' form if an explicit 'Address' form isn't found.
        match = next(
            (
                f
                for f in forms
                if f.get("name", "").lower() == "address"
                and f.get("subType", "").lower() == "fulltext"
            ),
            None,
        )

        if not match:
            match = next(
                (f for f in forms if f.get("subType", "").lower() == "fulltext"), None
            )

        if not match or not match.get("templateId"):
            raise IntraMapsSessionError(
                "Could not identify a valid FullText address form template."
            )

        self._address_form_template_id = match["templateId"]
        return self._address_form_template_id

    def search_address(self, address: str, suburb: str | None = None) -> dict[str, Any]:
        """
        Perform a full-text search for an address string.

        Args:
            address: The address string to look up (e.g., '20 Settlers Ave').
            suburb: Optional suburb name to prefer in results when multiple
                    matches are returned (case-insensitive).

        Returns:
            The dictionary representing the first match found by the server.
        """
        form_id = self._get_form_template_id()

        params = {
            "infoPanelWidth": "0",
            "mode": "Refresh",
            "form": form_id,
            "resubmit": "false",
            "IntraMapsSession": self.intramaps_session,
        }
        if self.cfg.selection_layer_filter:
            params["selectionLayersFilter"] = self.cfg.selection_layer_filter

        self.log.info(f"Searching address: {address}")
        r = self._session.post(
            self._url("/ApplicationEngine/Search/"),
            params=params,
            json={"fields": [address]},
            timeout=self.cfg.timeout_s,
        )
        r.raise_for_status()

        results = r.json().get("fullText", [])
        if not results:
            raise IntraMapsSearchError(f"No results found for address: {address}")

        # If a suburb is provided, prefer results that mention it
        if suburb and suburb.strip():
            suburb_lower = suburb.strip().casefold()
            for result in results:
                display = str(result.get("displayValue", "")).casefold()
                if suburb_lower in display:
                    return result

        return results[0]

    def select_address(self, address: str, suburb: str | None = None) -> dict[str, Any]:
        """
        Orchestrates the full search-and-select workflow.

        This finds the address, extracts the database keys, and then tells the
        IntraMaps engine to 'Select' that feature on the map.

        Args:
            address: The target address.

        Returns:
            A result dictionary containing success status and the final API response.
        """
        result = self.search_address(address, suburb)

        # Extract required keys. GIS APIs often use inconsistent casing (dbkey vs dbKey).
        db_key = self._get_case_insensitive(result, "dbKey")
        if not db_key:
            raise IntraMapsSearchError("Search result missing critical 'dbKey'.")

        selection_layer = (
            self._get_case_insensitive(result, "selectionLayer")
            or self._get_case_insensitive(result, "selectionLayerId")
            or self.cfg.default_selection_layer
        )

        map_key = (
            self._get_case_insensitive(result, "mapKey") or self.cfg.default_map_key
        )

        payload = {
            "selectionLayer": str(selection_layer),
            "mapKey": str(map_key),
            "infoPanelWidth": -350,
            "mode": "Refresh",
            "dbKey": str(db_key),
            "zoomType": "current",
        }

        self.log.debug(f"Setting map selection for dbKey: {db_key}")
        r = self._session.post(
            self._url("/ApplicationEngine/Search/Refine/Set"),
            params={"IntraMapsSession": self.intramaps_session},
            json=payload,
            timeout=self.cfg.timeout_s,
        )
        r.raise_for_status()

        return {
            "status": "success",
            "dbKey": db_key,
            "response": (
                r.json()
                if "application/json" in r.headers.get("Content-Type", "")
                else r.text
            ),
        }

    @staticmethod
    def _get_case_insensitive(data: dict[str, Any], key: str) -> Any | None:
        """Safely retrieves a value from a dictionary regardless of key casing."""
        k_lower = key.lower()
        for k, v in data.items():
            if k.lower() == k_lower:
                return v
        return None

    def __enter__(self) -> MapsClient:
        """Supports the 'with' statement for automatic resource cleanup."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the underlying network session when exiting the context."""
        self._session.close()


# --- Integration API Client ---


@dataclass(frozen=True)
class IntegrationClientConfig:
    """Configuration for the IntraMaps Integration (REST/apikey) API."""

    base_url: str
    instance: str = "IntraMaps23A"
    api_key: str = ""
    config_id: str = "00000000-0000-0000-0000-000000000000"
    project: str = ""
    timeout_s: int = 25


class IntegrationClient:
    """Client for the IntraMaps Integration API (apikey-authenticated REST)."""

    def __init__(self, config: IntegrationClientConfig):
        self.cfg = config

    def _url(self, path: str) -> str:
        base = self.cfg.base_url.rstrip("/")
        return f"{base}/{self.cfg.instance}/ApplicationEngine/Integration/api{path}"

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self.cfg.api_key:
            h["Authorization"] = f"apikey {self.cfg.api_key}"
        return h

    def search(self, form_id: str, fields: str) -> dict[str, str]:
        """Search using an Integration API form.

        Returns a name→value dict from the first result.
        """
        params: dict[str, str] = {
            "configId": self.cfg.config_id,
            "form": form_id,
            "fields": fields,
        }
        if self.cfg.project:
            params["project"] = self.cfg.project

        r = requests.get(
            self._url("/search/"),
            params=params,
            headers=self._headers(),
            timeout=self.cfg.timeout_s,
        )
        r.raise_for_status()
        results = r.json()

        if not results or not results[0]:
            raise IntraMapsSearchError(f"No results found for: {fields}")

        return {item["name"]: item["value"] for item in results[0]}

    def search_all(self, form_id: str, fields: str) -> list[dict[str, str]]:
        """Search returning all results as a list of name→value dicts."""
        params: dict[str, str] = {
            "configId": self.cfg.config_id,
            "form": form_id,
            "fields": fields,
        }
        if self.cfg.project:
            params["project"] = self.cfg.project

        r = requests.get(
            self._url("/search/"),
            params=params,
            headers=self._headers(),
            timeout=self.cfg.timeout_s,
        )
        r.raise_for_status()
        results = r.json()

        if not results:
            raise IntraMapsSearchError(f"No results found for: {fields}")

        return [{item["name"]: item["value"] for item in result} for result in results]

    def reproject(
        self, x: float, y: float, epsg_in: str, epsg_out: str
    ) -> dict[str, Any]:
        """Reproject coordinates between coordinate systems."""
        params = {
            "configId": self.cfg.config_id,
            "project": self.cfg.project,
            "x": str(x),
            "y": str(y),
            "epsg": epsg_in,
            "epsgout": epsg_out,
        }
        r = requests.get(
            self._url("/Reproject"),
            params=params,
            headers=self._headers(),
            timeout=self.cfg.timeout_s,
        )
        r.raise_for_status()
        return r.json()


# --- Helpers ---


def extract_panel_fields(
    response: dict[str, Any], panel_key: str = "info1"
) -> dict[str, str]:
    """Extract a name→value dict from an IntraMaps infoPanels response.

    Handles the nested structure: infoPanels > panel_key > feature > fields,
    where each field has a name/caption and a value dict with a 'value' key.
    """
    fields = (
        response.get("infoPanels", {})
        .get(panel_key, {})
        .get("feature", {})
        .get("fields", [])
    )
    result: dict[str, str] = {}
    for field in fields:
        name = field.get("name") or field.get("caption", "")
        value = field.get("value", {})
        if isinstance(value, dict):
            result[name] = value.get("value", "")
        elif isinstance(value, str):
            result[name] = value
    return result
