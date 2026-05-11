"""
ArcGIS REST API Client Library.

Provides reusable helpers for interacting with ArcGIS services:
  - Geocoding addresses via the ArcGIS World GeocodeServer
  - Querying ArcGIS Feature Services with spatial or attribute filters

Typical workflow:
    1. Call geocode() to turn an address string into coordinates.
    2. Call query_feature_layer() with those coordinates to retrieve
       attributes from a FeatureServer layer.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"


class ArcGisError(Exception):
    """Base exception for ArcGIS-related failures."""


class ArcGisGeocodeError(ArcGisError):
    """Raised when geocoding fails or returns no candidates."""


class ArcGisQueryError(ArcGisError):
    """Raised when a feature layer query fails or returns no features."""


def geocode(
    address: str,
    *,
    geocode_url: str = GEOCODE_URL,
    out_sr: int = 4326,
    max_locations: int = 1,
    timeout: int = 20,
) -> dict[str, float]:
    """Geocode an address string to coordinates.

    Args:
        address: Free-text address to geocode.
        geocode_url: Base URL of the GeocodeServer (defaults to Esri World).
        out_sr: Output spatial reference WKID (default 4326 = WGS84).
        max_locations: Maximum number of candidates to request.
        timeout: Request timeout in seconds.

    Returns:
        dict with 'x' and 'y' keys (longitude and latitude for WKID 4326).

    Raises:
        ArcGisGeocodeError: If no candidates are found.
    """
    params: dict[str, Any] = {
        "SingleLine": address,
        "outSR": json.dumps({"wkid": out_sr}),
        "maxLocations": max_locations,
        "f": "json",
    }

    r = requests.get(
        f"{geocode_url.rstrip('/')}/findAddressCandidates",
        params=params,
        timeout=timeout,
    )
    r.raise_for_status()

    candidates = r.json().get("candidates", [])
    if not candidates:
        raise ArcGisGeocodeError(f"No candidates found for: {address}")

    location = candidates[0]["location"]
    _LOGGER.debug("Geocoded '%s' -> (%s, %s)", address, location["x"], location["y"])
    return location


def query_feature_layer(
    feature_url: str,
    *,
    geometry: dict[str, Any] | None = None,
    geometry_type: str = "esriGeometryPoint",
    spatial_rel: str = "esriSpatialRelIntersects",
    where: str | None = None,
    out_fields: str = "*",
    return_geometry: bool = False,
    in_sr: int = 4326,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Query an ArcGIS FeatureServer layer.

    Supports both spatial queries (point-in-polygon) and attribute queries.

    Args:
        feature_url: Full URL to the FeatureServer layer
            (e.g. '.../FeatureServer/0').
        geometry: Geometry dict for spatial queries (e.g. {'x': ..., 'y': ...}).
        geometry_type: ArcGIS geometry type string.
        spatial_rel: Spatial relationship for the query.
        where: SQL where clause for attribute queries.
        out_fields: Comma-separated field names or '*' for all.
        return_geometry: Whether to include geometry in the response.
        in_sr: Input spatial reference WKID for the geometry.
        timeout: Request timeout in seconds.

    Returns:
        List of attribute dicts, one per matching feature.

    Raises:
        ArcGisQueryError: If no features are found.
    """
    params: dict[str, Any] = {
        "outFields": out_fields,
        "returnGeometry": str(return_geometry).lower(),
        "f": "json",
    }

    if geometry is not None:
        params["geometry"] = json.dumps(geometry)
        params["geometryType"] = geometry_type
        params["spatialRel"] = spatial_rel
        params["inSR"] = str(in_sr)

    if where is not None:
        params["where"] = where

    r = requests.get(
        f"{feature_url.rstrip('/')}/query",
        params=params,
        timeout=timeout,
    )
    r.raise_for_status()

    features = r.json().get("features", [])
    if not features:
        raise ArcGisQueryError("No features found for the given query.")

    return [f.get("attributes", {}) for f in features]


def epoch_ms_to_date(epoch_ms: int | float) -> date:
    """Convert an ArcGIS epoch-millisecond timestamp to a Python date."""
    return date.fromtimestamp(epoch_ms / 1000)


def get_next_n_dates(start: date, n: int, delta: timedelta) -> list[date]:
    """
    Starting from `start`, advance past today by `delta` steps, then
    collect the next `n` dates (each `delta` apart).
    """
    d = start
    today = date.today()
    result: list[date] = []
    for _ in range(n):
        while d < today:
            d += delta
        result.append(d)
        d += delta
    return result


def most_recent_weekday(day_of_week: int) -> date:
    """
    Return the most recent (including today) occurrence of `day_of_week`
    (0=Monday … 6=Sunday).
    """
    today = date.today()
    return today - timedelta((today.weekday() - day_of_week + 7) % 7)
