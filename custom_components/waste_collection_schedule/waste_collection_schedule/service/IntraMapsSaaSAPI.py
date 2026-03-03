"""
Utility module for accessing the IntraMapsSaaS API.

Example usage:

>>> from waste_collection_schedule.service import IntraMapsSaaSAPI

>>> address = "28 Wem Mews"
>>> suburb = "High Wycombe"

>>> config = IntraMapsSaaSAPI.MapsClientConfig(
>>>     base_url="https://kalamunda.spatial.t1cloud.com",
>>>     instance="spatial/intramaps",
>>>     config_id="38999f30-1676-4524-b501-0130581a2ba2",
>>>     project="d44a7973-329f-4626-9e09-35afeacc8724",
>>> )

>>> try:
>>>     with IntraMapsSaaSAPI.MapsClientSaaS(config) as client:
>>>         api_resp = client.select_address(address, suburb)
>>> except IntraMapsSaaSAPI.IntraMapsSearchError as e:
>>>     raise Exception(f"No results found for address: {address}") from e
>>> except IntraMapsSaaSAPI.IntraMapsError as e:
>>>     raise Exception(f"IntraMaps Operation Failed: {e}") from e

NOTE: The client config is extracted manually via inspecting Kalamunda bin collection website (same process could be used for other
councils using the same service).
"""

# flake8: noqa: F401

from typing import Any, Optional

from waste_collection_schedule.service.RockinghamCityMaps import (
    IntraMapsError,
    IntraMapsSearchError,
    MapsClient,
    MapsClientConfig,
)


class MapsClientSaaS(MapsClient):
    """
    A stateful client for the IntraMaps cloud based SaaS API.

    This client manages the 'X-IntraMaps-Session' token, discovers form metadata
    automatically, and provides high-level methods for address resolution.

    Inherits from the base implementation in RockinghamCityMaps.py
    """

    def search_address(
        self, address: str, suburb: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Perform a full-text search for an address string.

        Args:
            address: The address string to look up (e.g., '20 Settlers Ave').
            suburb: Optional string containing suburb if search can't include it.

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

        for found_address in results:
            if suburb in found_address.get("displayValue", ""):
                return found_address

        return results[0]

    def select_address(
        self, address: str, suburb: Optional[str] = None
    ) -> dict[str, Any]:
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
