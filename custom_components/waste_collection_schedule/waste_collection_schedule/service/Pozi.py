"""
Pozi GIS Service platform (BaseSource architecture).

Pozi hosts council waste-collection lookups two ways, both resolved by a
point (lat/lng):

  GeoJSON zones (e.g. Frankston, Bendigo):
      A static GeoJSON file of zone polygons is fetched once; the point
      (given directly, or geocoded from an address first) is matched
      client-side via point-in-polygon. ``PoziGeoJsonRetriever`` does the
      acquisition (the GeoJSON GET, plus an optional geocode GET);
      ``PoziGeoJsonParser`` does the point-in-polygon match (no I/O).

  WFS spatial query (e.g. Vincent):
      The point (geocoded from an address via the ArcGIS World GeocodeServer)
      is sent to a Pozi QGIS WFS endpoint as a server-side spatial-intersects
      filter. ``PoziWfsRetriever`` issues both requests; ``PoziWfsParser``
      extracts the matching feature's properties (no I/O).

Both parsers return the matching zone's ``properties`` dict as a 0- or
1-item list (``[]`` when the point matched nothing), for a source's
``preprocess = preprocessors.RecurrenceExpander(_describe)`` to expand into
concrete collection dates. An address/lookup source built on either
retriever should set ``RAISE_ON_EMPTY = True`` so a point outside every zone
(or an address WFS finds nothing for) surfaces as a clear argument error
instead of a silently-empty schedule.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypedDict

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_LOGGER = logging.getLogger(__name__)


class _FeatureCollection(TypedDict):
    """The GeoJSON/WFS ``FeatureCollection`` shape every parser here relies on."""

    features: list


# --------------------------------------------------------------------------- #
# GeoJSON zone lookup (client-side point-in-polygon)
# --------------------------------------------------------------------------- #


class PoziGeoJsonRetriever(RetrieverFunc):
    """Fetch a Pozi GeoJSON zone file and return it alongside the query point.

    Two ways to get the point (give exactly one):

    * ``lat`` / ``lon`` -- ``source.params`` field names holding the point
      directly (e.g. a ``config_params.coords()`` param).
    * ``address`` -- a ``source.params`` field name holding a free-text
      address, resolved to a point by ``geocode`` (a
      ``callable(address, source) -> (lat, lng)``, e.g. :func:`geocode_earth`).

    Returns ``(response, lat, lng)`` raw -- the point-in-polygon match itself
    is pure computation, done by :class:`PoziGeoJsonParser` with no further
    I/O. Pair the two.
    """

    def __init__(
        self,
        url: str,
        *,
        lat: str | None = "lat",
        lon: str | None = "lon",
        address: str | None = None,
        geocode: Callable[[str, BaseSource], tuple[float, float]] | None = None,
        timeout: int = 20,
    ):
        self.url = url
        self.lat = None if address is not None else lat
        self.lon = None if address is not None else lon
        self.address = address
        self.geocode = geocode
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> tuple[Response, float, float]:
        if self.address is not None:
            if self.geocode is None:
                raise SourceArgumentNotFound(
                    self.address, None, "no geocoder configured for this source"
                )
            address_value = source.params[self.address]
            lat, lng = self.geocode(address_value, source)
        else:
            assert self.lat is not None and self.lon is not None
            lat = float(source.params[self.lat])
            lng = float(source.params[self.lon])

        response = source.session.get(self.url, timeout=self.timeout)
        return response, lat, lng


class PoziGeoJsonParser(Parser["list[dict[str, Any]]"]):
    """Match the query point against GeoJSON zone polygons; no I/O.

    Returns the matching zone's ``properties`` as a 0- or 1-item list: ``[]``
    when the point falls outside every zone (an address/lookup source then
    relies on ``RAISE_ON_EMPTY`` to surface that as a clear argument error,
    rather than this parser guessing which argument was at fault).
    """

    def __call__(
        self,
        raw: tuple[Response, float, float],
        source: BaseSource | None = None,
    ) -> list[dict[str, Any]]:
        response, lat, lng = raw
        response.raise_for_status()
        data = response_shape.validate(
            response.json(),
            _FeatureCollection,
            source_name=response_shape.source_name(source),
        )
        features = data["features"]
        response_shape.expect(
            bool(features),
            source_name=response_shape.source_name(source),
            detail="Pozi GeoJSON zone file has no features",
            raw=data,
        )

        for feature in features:
            if _point_in_geometry(lat, lng, feature.get("geometry", {})):
                _LOGGER.debug(
                    "Point (%s, %s) matched zone: %s",
                    lat,
                    lng,
                    feature.get("properties", {}),
                )
                return [feature.get("properties", {})]
        return []


def geocode_earth(
    address: str,
    source: BaseSource,
    *,
    api_key: str,
    boundary_gid: str | None = None,
    layers: str = "address,street",
    timeout: int = 20,
) -> tuple[float, float]:
    """Geocode an address via geocode.earth's autocomplete endpoint.

    Ahead of a :class:`PoziGeoJsonRetriever` lookup for a provider whose Pozi
    widget resolves a point but not an address itself (e.g. Frankston).
    Returns ``(lat, lng)``. Raises ``SourceArgumentNotFound`` when no
    candidate is found.
    """
    params: dict[str, str] = {"text": address, "api_key": api_key, "layers": layers}
    if boundary_gid is not None:
        params["boundary.gid"] = boundary_gid

    response = source.session.get(
        "https://api.geocode.earth/v1/autocomplete", params=params, timeout=timeout
    )
    response.raise_for_status()

    features = response.json().get("features", [])
    if not features:
        raise SourceArgumentNotFound("address", address)

    lng, lat = features[0]["geometry"]["coordinates"]
    return lat, lng


def _point_in_geometry(lat: float, lng: float, geometry: dict) -> bool:
    """Check if a point lies within a GeoJSON geometry (Polygon or MultiPolygon)."""
    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        return _point_in_polygon(lng, lat, coords[0])
    if geom_type == "MultiPolygon":
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
    xinters = 0.0

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


# --------------------------------------------------------------------------- #
# WFS spatial query (server-side intersects filter)
# --------------------------------------------------------------------------- #


class PoziWfsRetriever(RetrieverFunc):
    """Geocode an address (ArcGIS), then query a Pozi QGIS WFS layer.

    Pozi's WFS endpoint has no address lookup of its own, so this always
    geocodes first via ``waste_collection_schedule.service.ArcGis.geocode``
    (the shared ArcGIS World GeocodeServer helper), then issues a
    spatial-intersects ``GetFeature`` request against the given WFS layer.
    Returns the raw HTTP Response; pair with :class:`PoziWfsParser`.
    """

    def __init__(
        self,
        base_url: str,
        map_path: str,
        typename: str,
        *,
        address: str = "address",
        timeout: int = 20,
    ):
        self.base_url = base_url
        self.map_path = map_path
        self.typename = typename
        self.address = address
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        from waste_collection_schedule.service.ArcGis import (
            ArcGisGeocodeError,
            geocode,
        )

        address_value = source.params[self.address]
        try:
            location = geocode(address_value)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound(self.address, address_value) from e

        wfs_filter = (
            "<Filter>"
            "<Intersects>"
            "<PropertyName>geom</PropertyName>"
            '<Point xmlns="http://www.opengis.net/gml" srsName="EPSG:4326">'
            f'<pos srsDimension="2">{location["x"]} {location["y"]}</pos>'
            "</Point>"
            "</Intersects>"
            "</Filter>"
        )
        params: dict[str, str] = {
            "MAP": self.map_path,
            "TYPENAME": self.typename,
            "LAYERS": self.typename.replace("_", " "),
            "STYLES": "default",
            "SERVICE": "WFS",
            "REQUEST": "GetFeature",
            "VERSION": "1.1.0",
            "SRSNAME": "EPSG:4326",
            "OUTPUTFORMAT": "application/json",
            "FILTER": wfs_filter,
        }
        return source.session.get(self.base_url, params=params, timeout=self.timeout)


class PoziWfsParser(Parser["list[dict[str, Any]]"]):
    """Extract the first matching feature's properties from a WFS response.

    No I/O. Returns ``[]`` when the spatial filter matched nothing -- a
    legitimate "address outside the service area" result, not a shape
    change, so an address/lookup source relies on ``RAISE_ON_EMPTY`` rather
    than this parser raising.
    """

    def __call__(
        self,
        response: Response,
        source: BaseSource | None = None,
    ) -> list[dict[str, Any]]:
        response.raise_for_status()
        data = response_shape.validate(
            response.json(),
            _FeatureCollection,
            source_name=response_shape.source_name(source),
        )
        features = data["features"]
        if not features:
            return []
        props = features[0].get("properties", {})
        _LOGGER.debug("WFS query matched: %s", props)
        return [props]
