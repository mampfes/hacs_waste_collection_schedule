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

import json
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
    Configuration schema for the RockinghamCityMaps Client.

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

            # Extract the first available module to act as our operational context
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

    def search_address(self, address: str) -> dict[str, Any]:
        """
        Perform a full-text search for an address string.

        Args:
            address: The address string to look up (e.g., '20 Settlers Ave').

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

        return results[0]

    def select_address(self, address: str) -> dict[str, Any]:
        """
        Orchestrates the full search-and-select workflow.

        This finds the address, extracts the database keys, and then tells the
        IntraMaps engine to 'Select' that feature on the map.

        Args:
            address: The target address.

        Returns:
            A result dictionary containing success status and the final API response.
        """
        result = self.search_address(address)

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


# --- Execution Example ---

if __name__ == "__main__":
    # Configure logging for console output
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Initialize config for Rockingham WA instance
    config = MapsClientConfig(
        base_url="https://maps.rockingham.wa.gov.au",
        project="1917ad36-6a1d-4145-9eeb-736f8fa9646d",
    )

    try:
        # Use context manager to ensure the network session is closed properly
        with MapsClient(config) as client:
            res = client.select_address("13 Settlers Avenue BALDIVIS")
            print("\nFinal API Selection Response:")
            print(json.dumps(res, indent=2))

    except IntraMapsError as e:
        logging.error(f"IntraMaps Operation Failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected System Error: {e}")
