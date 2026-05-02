"""
Pozi GIS Service Library.

Provides reusable helpers for interacting with Pozi-based council GIS services:
  - Querying GeoJSON zone layers hosted on connect.pozi.com
  - Querying QGIS WFS endpoints via Pozi server-side spatial filters
  - Client-side point-in-polygon matching for GeoJSON zone lookups

Typical workflows:

  GeoJSON zones (e.g. Frankston, Bendigo):
      1. Call query_geojson_zones() with the connect.pozi.com URL and coordinates.
      2. Receive the properties dict of the matching zone feature.

  WFS spatial query (e.g. Vincent):
      1. Call query_wfs_layer() with the QGIS server URL, map path, layer name,
         and coordinates.
      2. Receive the properties dict of the matching feature.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

_LOGGER = logging.getLogger(__name__)


class PoziError(Exception):
    """Base exception for Pozi-related failures."""


class PoziGeoJsonError(PoziError):
    """Raised when a GeoJSON zone query fails or returns no match."""


class PoziWfsError(PoziError):
    """Raised when a WFS query fails or returns no features."""


def query_geojson_zones(
    url: str,
    lat: float,
    lng: float,
    *,
    timeout: int = 20,
) -> dict[str, Any]:
    """Fetch GeoJSON zones and find the zone containing the given point.

    Args:
        url: Full URL to a GeoJSON file (typically on connect.pozi.com).
        lat: Latitude of the point.
        lng: Longitude of the point.
        timeout: Request timeout in seconds.

    Returns:
        Properties dict of the matching feature.

    Raises:
        PoziGeoJsonError: If no zone contains the point.
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    features = data.get("features", [])
    if not features:
        raise PoziGeoJsonError(f"No features found in GeoJSON from {url}")

    for feature in features:
        geometry = feature.get("geometry", {})
        if _point_in_geometry(lat, lng, geometry):
            _LOGGER.debug(
                "Point (%s, %s) matched zone: %s",
                lat,
                lng,
                feature.get("properties", {}),
            )
            return feature.get("properties", {})

    raise PoziGeoJsonError(f"Point ({lat}, {lng}) not found in any zone from {url}")


def query_wfs_layer(
    base_url: str,
    map_path: str,
    typename: str,
    lat: float,
    lng: float,
    *,
    timeout: int = 20,
) -> dict[str, Any]:
    """Query a Pozi QGIS WFS endpoint with a spatial intersects filter.

    Args:
        base_url: Base URL of the QGIS WFS server
            (e.g. 'https://mapping.vincent.wa.gov.au/pozi/qgisserver').
        map_path: Server-side path to the QGIS project file
            (e.g. 'C:/Pozi/Waste.qgs').
        typename: WFS typename / layer name (e.g. 'Waste_Collection').
        lat: Latitude of the point (EPSG:4326).
        lng: Longitude of the point (EPSG:4326).
        timeout: Request timeout in seconds.

    Returns:
        Properties dict of the first matching feature.

    Raises:
        PoziWfsError: If no features are found.
    """
    wfs_filter = (
        "<Filter>"
        "<Intersects>"
        "<PropertyName>geom</PropertyName>"
        '<Point xmlns="http://www.opengis.net/gml" srsName="EPSG:4326">'
        f'<pos srsDimension="2">{lng} {lat}</pos>'
        "</Point>"
        "</Intersects>"
        "</Filter>"
    )

    params: dict[str, str] = {
        "MAP": map_path,
        "TYPENAME": typename,
        "LAYERS": typename.replace("_", " "),
        "STYLES": "default",
        "SERVICE": "WFS",
        "REQUEST": "GetFeature",
        "VERSION": "1.1.0",
        "SRSNAME": "EPSG:4326",
        "OUTPUTFORMAT": "application/json",
        "FILTER": wfs_filter,
    }

    r = requests.get(base_url, params=params, timeout=timeout)
    r.raise_for_status()

    data = r.json()
    features = data.get("features", [])
    if not features:
        raise PoziWfsError(
            f"No features found for point ({lat}, {lng}) in layer {typename}"
        )

    props = features[0].get("properties", {})
    _LOGGER.debug("WFS query matched: %s", props)
    return props


def _point_in_geometry(lat: float, lng: float, geometry: dict) -> bool:
    """Check if a point lies within a GeoJSON geometry (Polygon or MultiPolygon)."""
    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        return _point_in_polygon(lng, lat, coords[0])
    elif geom_type == "MultiPolygon":
        return any(_point_in_polygon(lng, lat, ring[0]) for ring in coords)

    return False


def _point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    """Ray-casting point-in-polygon test.

    Args:
        x: X coordinate (longitude) of the point.
        y: Y coordinate (latitude) of the point.
        polygon: List of [x, y] coordinate pairs forming the polygon ring.

    Returns:
        True if the point is inside the polygon.
    """
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside
