"""
ArcGIS REST API client for the BaseSource pipeline.

Provides:
  - geocode(): turn an address string into coordinates via the World GeocodeServer
  - feature_query(): GET a FeatureServer ``/query`` (spatial or attribute) and
    return the raw HTTP Response
  - ArcGisFeatureRetriever / ArcGisFeatureParser: the pipeline stages a source
    declares (retrieve returns the raw Response; parse extracts attributes)

Sources that project recurring schedules use the core ``recurrence`` helpers; a
source hitting several layers keeps its own ``retrieve`` and calls
feature_query() per layer.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Callable

import requests

from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"


class ArcGisError(Exception):
    """Base exception for ArcGIS-related failures."""


class ArcGisGeocodeError(ArcGisError):
    """Raised when geocoding fails or returns no candidates."""


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


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# These let an ArcGIS-backed source compose the platform declaratively while
# keeping retrieval and parsing strictly separate:
#
#     retrieve = ArcGisFeatureRetriever(FEATURE_URL, address="address")
#     parse    = ArcGisFeatureParser()
#
# ArcGisFeatureRetriever returns the *raw* /query HTTP Response (it resolves the
# address to a point internally, which is request-building, not data parsing).
# ArcGisFeatureParser turns that raw Response into the list of feature-attribute
# dicts. Either side can be swapped independently — e.g. the parser can run
# against a cached Response fixture, and the retriever can feed a different
# parser if a layer ever returns a different shape.
# --------------------------------------------------------------------------- #


def feature_query(
    feature_url: str,
    *,
    geometry: dict[str, Any] | None = None,
    where: str | None = None,
    out_fields: str = "*",
    in_sr: int = 4326,
    timeout: int = 20,
) -> Response:
    """GET a FeatureServer ``/query`` and return the *raw* Response (unparsed).

    The low-level acquisition primitive — supports both a spatial point query
    (``geometry``) and an attribute query (``where``). Pair with
    :class:`ArcGisFeatureParser`. A source that must hit several layers calls
    this once per layer from its own ``retrieve``.
    """
    params: dict[str, Any] = {
        "outFields": out_fields,
        "returnGeometry": "false",
        "f": "json",
    }
    if geometry is not None:
        params["geometry"] = json.dumps(geometry)
        params["geometryType"] = "esriGeometryPoint"
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = str(in_sr)
    if where is not None:
        params["where"] = where
    return requests.get(
        f"{feature_url.rstrip('/')}/query", params=params, timeout=timeout
    )


class ArcGisFeatureRetriever(RetrieverFunc):
    """GET a single FeatureServer layer and return the raw Response.

    Two modes (give exactly one):

    * ``address`` — geocode the address param to a point and run a spatial query;
    * ``where``   — run an attribute query (a SQL clause; a string, or a callable
      resolved against ``**source.params``).

    Pair with :class:`ArcGisFeatureParser`. Multi-layer sources keep their own
    ``retrieve`` and call :func:`feature_query` per layer.

    Args:
        feature_url: Full FeatureServer layer URL (e.g. ``.../FeatureServer/0``).
        address: ``source.params`` field with the address, or a callable.
        where: SQL where clause (string) or a callable returning one.
        out_fields: Comma-separated field names, or ``"*"`` for all.
        in_sr: Input spatial reference WKID for the geocoded point.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        feature_url: str,
        address: str | Callable[..., str] | None = "address",
        where: str | Callable[..., str] | None = None,
        out_fields: str = "*",
        in_sr: int = 4326,
        timeout: int = 20,
    ):
        self.feature_url = feature_url
        self.address = None if where is not None else address
        self.where = where
        self.out_fields = out_fields
        self.in_sr = in_sr
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        if self.where is not None:
            where = self.where(**source.params) if callable(self.where) else self.where
            return feature_query(
                self.feature_url,
                where=where,
                out_fields=self.out_fields,
                timeout=self.timeout,
            )

        if callable(self.address):
            address = self.address(**source.params)
        elif self.address is None:
            raise SourceArgumentNotFound(
                "address", "no address field or where clause configured"
            )
        else:
            address = source.params[self.address]
        try:
            location = geocode(address)
        except ArcGisGeocodeError as e:
            field = self.address if isinstance(self.address, str) else "address"
            raise SourceArgumentNotFound(field, address) from e
        return feature_query(
            self.feature_url,
            geometry=location,
            out_fields=self.out_fields,
            in_sr=self.in_sr,
            timeout=self.timeout,
        )


class ArcGisFeatureParser(Parser[list[dict[str, Any]]]):
    """Extract feature-attribute dicts from an ArcGIS ``/query`` Response.

    Returns one ``attributes`` dict per matching feature (an empty list when the
    point matched no feature). Pair with :class:`ArcGisFeatureRetriever`.
    """

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        response.raise_for_status()
        features = response.json().get("features", [])
        return [feature.get("attributes", {}) for feature in features]


class ArcGisMultiFeatureRetriever(RetrieverFunc):
    """Geocode once, then spatially query several FeatureServer layers.

    For councils whose services live on separate layers (one per bin type, or
    per zone). Returns a list of ``(label, raw Response)`` pairs — one per layer
    — so multi-layer sources stay declarative instead of hand-rolling ``retrieve``.
    Pair with :class:`ArcGisMultiFeatureParser`.

    Args:
        layers: an iterable of ``(label, feature_url)`` or
            ``(label, feature_url, out_fields)`` — ``label`` is carried through to
            each record (typically the waste-type key). A ``dict`` of
            ``{label: feature_url}`` is also accepted.
        address: ``source.params`` field with the address, or a callable.
        out_fields: default field list for layers that don't specify their own.
        in_sr: input spatial reference WKID for the geocoded point.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        layers,
        address: str | Callable[..., str] = "address",
        out_fields: str = "*",
        in_sr: int = 4326,
        timeout: int = 20,
    ):
        # Normalise to (label, url, out_fields) triples.
        self.layers: list[tuple[Any, str, str]] = []
        if isinstance(layers, dict):
            self.layers = [(label, url, out_fields) for label, url in layers.items()]
        else:
            for entry in layers:
                parts: list[Any] = list(entry)
                fields = parts[2] if len(parts) > 2 else out_fields
                self.layers.append((parts[0], parts[1], fields))
        self.address = address
        self.in_sr = in_sr
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> list[tuple[Any, Response]]:
        address = (
            self.address(**source.params)
            if callable(self.address)
            else source.params[self.address]
        )
        try:
            location = geocode(address)
        except ArcGisGeocodeError as e:
            field = self.address if isinstance(self.address, str) else "address"
            raise SourceArgumentNotFound(field, address) from e

        # Query each layer independently and tolerate a single failing layer
        # (HTTP/connection error) by skipping it, so one bad layer doesn't abort
        # the whole fetch — matching the per-layer try/except councils relied on.
        results: list[tuple[Any, Response]] = []
        for label, url, fields in self.layers:
            try:
                response = feature_query(
                    url,
                    geometry=location,
                    out_fields=fields,
                    in_sr=self.in_sr,
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException as err:
                _LOGGER.debug("ArcGIS layer %s failed, skipping: %s", url, err)
                continue
            results.append((label, response))
        return results


class ArcGisMultiFeatureParser(Parser[list[tuple[Any, dict[str, Any]]]]):
    """Extract ``(label, attributes)`` records from labelled multi-layer responses.

    Consumes the ``[(label, Response), ...]`` produced by
    :class:`ArcGisMultiFeatureRetriever` and yields one ``(label, attributes)``
    per matching feature; layers whose point matched nothing are skipped.
    """

    def __call__(
        self,
        responses: list[tuple[Any, Response]],
        source: BaseSource | None = None,
    ) -> list[tuple[Any, dict[str, Any]]]:
        records: list[tuple[Any, dict[str, Any]]] = []
        for label, response in responses:
            response.raise_for_status()
            for feature in response.json().get("features", []):
                records.append((label, feature.get("attributes", {})))
        return records
