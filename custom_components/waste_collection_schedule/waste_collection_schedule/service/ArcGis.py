"""
ArcGIS REST API client for the BaseSource pipeline.

Provides:
  - geocode(): turn an address string into coordinates via the World GeocodeServer
  - feature_query(): GET a FeatureServer ``/query`` (spatial or attribute) and
    return the raw HTTP Response
  - ArcGisFeatureRetriever / ArcGisFeatureParser: the pipeline stages a source
    declares (retrieve returns the raw Response; parse extracts attributes)
  - ArcGisMultiFeatureRetriever / ArcGisMultiFeatureParser: the same for a
    source whose layers are split (one per bin type / zone)
  - ArcGisTwoStepFeatureRetriever: a two-step attribute query (locate a record's
    id via one ``where`` clause, then fetch the full record by that id)
  - coords_point(): use a lat/lon already in ``source.params`` as the query
    point instead of geocoding an address
  - ArcGisDistinctValues: the distinct values of one field, for suggesting what
    a no-match input should have been
  - geocoded_params(): geocode an address into the query params of an ordinary
    (non-ArcGIS) endpoint, for a provider keyed by a point
  - ArcGisZoneParser / point_in_polygon(): match a geocoded address against a
    GeoJSON polygon set, for a council with no FeatureServer to query

Prefer these declarative stages over a hand-written ``retrieve``: a single-layer
source uses ``ArcGisFeatureRetriever`` (address-geocode, ``where`` clause or
``point``), a multi-layer source uses ``ArcGisMultiFeatureRetriever``, and both
pair with the matching parser so the ``FeatureEnvelope`` shape is validated in
one place. Reach for ``feature_query()``/``geocode()`` directly only for a
genuinely irregular flow the retrievers can't express, and still route the final
Response through ``ArcGisFeatureParser`` so the response-shape check is not
bypassed. Sources that project recurring schedules add the core ``recurrence``
helpers as a preprocess step; holiday adjustments go in a ``HolidayShift``
preprocess, not a custom retrieve.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import date
from typing import TYPE_CHECKING, Any, TypedDict

import requests

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Response, RetrieverFunc


class FeatureEnvelope(TypedDict):
    """The ArcGIS ``/query`` response shape every Feature parser relies on."""

    features: list


if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"


def epoch_ms_to_date(epoch_ms: int | float) -> date:
    """Convert an ArcGIS epoch-millisecond timestamp to a Python date."""
    return date.fromtimestamp(epoch_ms / 1000)


class ArcGisError(Exception):
    """Base exception for ArcGIS-related failures."""


class ArcGisGeocodeError(ArcGisError):
    """Raised when geocoding fails or returns no candidates."""


class ArcGisQueryError(ArcGisError):
    """Raised when a FeatureServer query matches no features."""


def geocode(
    address: str,
    *,
    geocode_url: str = GEOCODE_URL,
    out_sr: int = 4326,
    out_fields: str | None = None,
    max_locations: int = 1,
    timeout: int = 20,
) -> dict[str, Any]:
    """Geocode an address string to a point, with the candidate's attributes.

    Args:
        address: Free-text address to geocode.
        geocode_url: Base URL of the GeocodeServer (defaults to Esri World).
        out_sr: Output spatial reference WKID (default 4326 = WGS84).
        out_fields: Optional ``outFields`` to populate ``attributes`` (e.g.
            ``"City"`` or ``"*"``). Omit it when you only need the point.
        max_locations: Maximum number of candidates to request.
        timeout: Request timeout in seconds.

    Returns:
        A dict carrying the point coordinates (``x``/``y`` for WKID 4326) plus an
        ``attributes`` dict. Callers that only need the point read ``x``/``y``
        (:func:`feature_query` does exactly that and ignores the rest), so the
        return is a drop-in geometry; callers that also need a field (a city, a
        zone) pass ``out_fields`` and read ``result["attributes"]``.

    Raises:
        ArcGisGeocodeError: If no candidates are found.
    """
    params: dict[str, Any] = {
        "SingleLine": address,
        "outSR": json.dumps({"wkid": out_sr}),
        "maxLocations": max_locations,
        "f": "json",
    }
    if out_fields is not None:
        params["outFields"] = out_fields

    r = requests.get(
        f"{geocode_url.rstrip('/')}/findAddressCandidates",
        params=params,
        timeout=timeout,
    )
    r.raise_for_status()

    candidates = r.json().get("candidates", [])
    if not candidates:
        raise ArcGisGeocodeError(f"No candidates found for: {address}")

    best = candidates[0]
    location = best["location"]
    _LOGGER.debug("Geocoded '%s' -> (%s, %s)", address, location["x"], location["y"])
    return {**location, "attributes": best.get("attributes", {})}


def coords_point(lat: str = "lat", lon: str = "lon") -> Callable[..., dict[str, float]]:
    """Build a ``point`` resolver that reads a lat/lon pair from ``source.params``.

    For a council configured by a map pick (``config_params.coords()``) rather
    than a street address: there is nothing to geocode, the point is already in
    the params. Pass the result as the ``point`` argument of
    :class:`ArcGisFeatureRetriever` or :class:`ArcGisMultiFeatureRetriever`::

        retrieve = ArcGisMultiFeatureRetriever(LAYERS, point=coords_point())

    Args:
        lat: ``source.params`` field holding the latitude.
        lon: ``source.params`` field holding the longitude.
    """

    def resolve(**params: Any) -> dict[str, float]:
        return {"x": params[lon], "y": params[lat]}

    return resolve


def _resolve_address(
    address: str | Callable[..., str] | None, params: dict[str, Any]
) -> tuple[str, str]:
    """Resolve an address spec to ``(query string, argument name to blame)``."""
    if callable(address):
        return address(**params), "address"
    if address is None:
        raise SourceArgumentNotFound(
            "address", "no address field, point or where clause configured"
        )
    return params[address], address


def _locate(
    source: BaseSource,
    address: str | Callable[..., str] | None,
    point: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Resolve the point a spatial query runs at: params lat/lon, or a geocode."""
    if point is not None:
        return point(**source.params)
    query, field = _resolve_address(address, source.params)
    try:
        return geocode(query)
    except ArcGisGeocodeError as e:
        raise SourceArgumentNotFound(field, query) from e


def geocoded_params(
    address: str | Callable[..., str] = "address",
    *,
    lon_param: str = "lon",
    lat_param: str = "lat",
    extra: dict[str, Any] | None = None,
) -> Callable[..., dict[str, Any]]:
    """Build a request-params callable that geocodes an address to a point.

    For a provider that is not itself on ArcGIS but keys its endpoint by a
    lat/lon. Geocoding is request-building, so it belongs in the params of the
    shared HTTP retriever rather than in a source-local ``retrieve``::

        retrieve = retrievers.HttpGetRetriever(
            url=API_URL,
            params=ArcGis.geocoded_params(lon_param="lng"),
        )

    Args:
        address: ``source.params`` field holding the address, or a callable
            resolved against ``**source.params`` (use one to append the state or
            country the geocoder needs).
        lon_param / lat_param: the endpoint's query-parameter names for the point.
        extra: further query parameters merged in after the point.

    Returns:
        A callable suitable as the ``params`` argument of any shared retriever.
        A geocode miss is reported as a not-found on the address argument.
    """

    def resolve(**params: Any) -> dict[str, Any]:
        query, field = _resolve_address(address, params)
        try:
            location = geocode(query)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound(field, query) from e
        return {lon_param: location["x"], lat_param: location["y"], **(extra or {})}

    return resolve


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
        # Use only the point coordinates; geocode() returns a richer dict (with
        # an attributes map) and a caller may hand the whole thing straight in.
        params["geometry"] = json.dumps({"x": geometry["x"], "y": geometry["y"]})
        params["geometryType"] = "esriGeometryPoint"
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = str(in_sr)
    if where is not None:
        params["where"] = where
    return requests.get(
        f"{feature_url.rstrip('/')}/query", params=params, timeout=timeout
    )


def query_feature_layer(
    feature_url: str,
    *,
    geometry: dict[str, Any] | None = None,
    where: str | None = None,
    out_fields: str = "*",
    in_sr: int = 4326,
    timeout: int = 20,
) -> list[dict[str, Any]]:
    """Query a FeatureServer layer and return the feature attribute dicts.

    Backward-compatible convenience over :func:`feature_query` (which returns the
    raw Response) plus the standard envelope parse, for legacy sources that
    consume the attributes directly. Pipeline sources use ``ArcGisFeatureParser``
    instead. Raises :class:`ArcGisQueryError` when the query matches no features.
    """
    response = feature_query(
        feature_url,
        geometry=geometry,
        where=where,
        out_fields=out_fields,
        in_sr=in_sr,
        timeout=timeout,
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        raise ArcGisQueryError("No features found for the given query.")
    return [f.get("attributes", {}) for f in features]


class ArcGisFeatureRetriever(RetrieverFunc):
    """GET a single FeatureServer layer and return the raw Response.

    Three modes (give exactly one):

    * ``address`` — geocode the address param to a point and run a spatial query;
    * ``point``   — run the same spatial query at a lat/lon already in
      ``source.params`` (see :func:`coords_point`), with nothing to geocode;
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
        point: callable resolved against ``**source.params`` returning the
            ``{"x": lon, "y": lat}`` query point, bypassing the geocoder.
    """

    def __init__(
        self,
        feature_url: str,
        address: str | Callable[..., str] | None = "address",
        where: str | Callable[..., str] | None = None,
        out_fields: str = "*",
        in_sr: int = 4326,
        timeout: int = 20,
        *,
        point: Callable[..., dict[str, Any]] | None = None,
    ):
        self.feature_url = feature_url
        self.address = None if where is not None or point is not None else address
        self.where = where
        self.out_fields = out_fields
        self.in_sr = in_sr
        self.timeout = timeout
        self.point = point

    def __call__(self, source: BaseSource) -> Response:
        if self.where is not None:
            where = self.where(**source.params) if callable(self.where) else self.where
            return feature_query(
                self.feature_url,
                where=where,
                out_fields=self.out_fields,
                timeout=self.timeout,
            )

        location = _locate(source, self.address, self.point)
        return feature_query(
            self.feature_url,
            geometry=location,
            out_fields=self.out_fields,
            in_sr=self.in_sr,
            timeout=self.timeout,
        )


class ArcGisDistinctValues:
    """The distinct values of one field on a layer, as no-match suggestions.

    ArcGIS answers "what are the valid inputs?" itself: a ``/query`` with
    ``returnDistinctValues`` lists every value a field takes. Pass an instance as
    ``ArcGisFeatureParser(suggestions=...)`` so an attribute query that matched
    nothing tells the user the names the layer actually knows::

        parse = ArcGisFeatureParser(
            argument="area_name",
            suggestions=ArcGisDistinctValues(FEATURE_URL, "NOME"),
        )

    Best-effort: any failure yields no suggestions rather than masking the
    not-found error the user actually needs to see.

    Args:
        feature_url: Full FeatureServer layer URL (e.g. ``.../FeatureServer/0``).
        field: Field whose distinct values are offered.
        where: SQL clause narrowing the candidates (default: every feature).
        order_by: ``orderByFields`` for the query; defaults to ``field``.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        feature_url: str,
        field: str,
        *,
        where: str = "1=1",
        order_by: str | None = None,
        timeout: int = 30,
    ):
        self.feature_url = feature_url
        self.field = field
        self.where = where
        self.order_by = order_by or field
        self.timeout = timeout

    def __call__(self, source: BaseSource | None = None) -> list[str]:
        try:
            response = requests.get(
                f"{self.feature_url.rstrip('/')}/query",
                params={
                    "where": self.where,
                    "outFields": self.field,
                    "returnGeometry": "false",
                    "returnDistinctValues": "true",
                    "orderByFields": self.order_by,
                    "f": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return sorted(
                {
                    feature["attributes"][self.field]
                    for feature in response.json().get("features", [])
                    if feature.get("attributes", {}).get(self.field)
                }
            )
        except Exception:
            _LOGGER.debug("Could not list distinct %s values", self.field)
            return []


class ArcGisFeatureParser(Parser[list[dict[str, Any]]]):
    """Extract feature-attribute dicts from an ArcGIS ``/query`` Response.

    Returns one ``attributes`` dict per matching feature. By default a query
    that matched nothing returns an empty list; set ``argument`` to report it as
    a bad input on that config field instead, which is what an address- or
    name-keyed attribute query wants (the value simply isn't in the layer).
    Pair with :class:`ArcGisFeatureRetriever`.

    Args:
        argument: ``source.params`` field to blame when nothing matched. Leave
            unset to return an empty list, as before.
        suggestions: callable ``(source) -> list`` producing the values the user
            could have used, typically :class:`ArcGisDistinctValues`. Only
            consulted when ``argument`` is set.
    """

    def __init__(
        self,
        *,
        argument: str | None = None,
        suggestions: Callable[..., list] | None = None,
    ):
        self.argument = argument
        self.suggestions = suggestions

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        response.raise_for_status()
        data = response_shape.validate(
            response.json(),
            FeatureEnvelope,
            source_name=response_shape.source_name(source),
        )
        features = [feature.get("attributes", {}) for feature in data["features"]]
        if not features and self.argument is not None:
            value = source.params.get(self.argument) if source is not None else None
            if self.suggestions is not None:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.argument, value, self.suggestions(source)
                )
            raise SourceArgumentNotFound(self.argument, value)
        return features


class ArcGisTwoStepFeatureRetriever(RetrieverFunc):
    """Resolve a record id via one attribute query, then fetch the full record.

    The common ArcGIS "address ``LIKE`` -> ``OBJECTID`` -> full record" shape:
    one ``where`` clause locates the matching feature, a field is pulled from it
    (typically ``OBJECTID``), and a second ``where`` clause fetches the wanted
    fields for that id. Both requests run through :func:`feature_query` and the
    lookup response is validated by :class:`ArcGisFeatureParser`, so a no-match
    raises a clear argument error instead of an ``IndexError``.

    Args:
        feature_url: Full FeatureServer layer URL (e.g. ``.../FeatureServer/0``).
        lookup_where: SQL where clause for the lookup (string or a callable
            resolved against ``**source.params``).
        schedule_where: ``callable(key, **source.params) -> str`` building the
            second where clause from the extracted key.
        argument: ``source.params`` field name reported in the not-found error,
            and the value shown with it.
        id_field: feature field pulled from the first match (default ``OBJECTID``).
        lookup_fields: ``outFields`` for the lookup query.
        out_fields: ``outFields`` for the final schedule query.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        feature_url: str,
        *,
        lookup_where: str | Callable[..., str],
        schedule_where: Callable[..., str],
        argument: str = "address",
        id_field: str = "OBJECTID",
        lookup_fields: str = "*",
        out_fields: str = "*",
        timeout: int = 20,
    ):
        self.feature_url = feature_url
        self.lookup_where = lookup_where
        self.schedule_where = schedule_where
        self.argument = argument
        self.id_field = id_field
        self.lookup_fields = lookup_fields
        self.out_fields = out_fields
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        where = (
            self.lookup_where(**source.params)
            if callable(self.lookup_where)
            else self.lookup_where
        )
        lookup = feature_query(
            self.feature_url,
            where=where,
            out_fields=self.lookup_fields,
            timeout=self.timeout,
        )
        matches = ArcGisFeatureParser()(lookup, source)
        value = source.params.get(self.argument)
        if not matches:
            raise SourceArgumentNotFound(self.argument, value)
        key = matches[0][self.id_field]
        return feature_query(
            self.feature_url,
            where=self.schedule_where(key, **source.params),
            out_fields=self.out_fields,
            timeout=self.timeout,
        )


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
        point: callable resolved against ``**source.params`` returning the
            ``{"x": lon, "y": lat}`` query point, bypassing the geocoder (see
            :func:`coords_point`).
    """

    def __init__(
        self,
        layers,
        address: str | Callable[..., str] = "address",
        out_fields: str = "*",
        in_sr: int = 4326,
        timeout: int = 20,
        *,
        point: Callable[..., dict[str, Any]] | None = None,
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
        self.point = point

    def __call__(self, source: BaseSource) -> list[tuple[Any, Response]]:
        location = _locate(source, self.address, self.point)

        # Query each layer independently and tolerate a single failing layer
        # (HTTP/connection error) by skipping it, so one bad layer doesn't abort
        # the whole fetch — matching the per-layer try/except councils relied on.
        results: list[tuple[Any, Response]] = []
        last_error: requests.RequestException | None = None
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
                last_error = err
                continue
            results.append((label, response))
        # Tolerating one bad layer is fine, but if EVERY layer failed the
        # provider is down or has moved: surface that instead of returning a
        # silently-empty schedule that reads to the user as "no collections".
        if self.layers and not results:
            raise ArcGisError(
                f"all {len(self.layers)} ArcGIS layers failed to load"
            ) from last_error
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
        name = response_shape.source_name(source)
        for label, response in responses:
            response.raise_for_status()
            data = response_shape.validate(
                response.json(), FeatureEnvelope, source_name=name
            )
            for feature in data["features"]:
                records.append((label, feature.get("attributes", {})))
        return records


def point_in_polygon(x: float, y: float, ring: list) -> bool:
    """Ray-casting test: is ``(x, y)`` inside the ``[[x, y], ...]`` polygon ring?

    The geometry half of :class:`ArcGisZoneParser`, exposed because a council
    that ships its zones as polygons sometimes needs the test on its own.
    """
    n = len(ring)
    inside = False
    p1x, p1y = ring[0]
    for i in range(1, n + 1):
        p2x, p2y = ring[i % n]
        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class ArcGisZoneParser(Parser[list[dict[str, Any]]]):
    """Locate a geocoded address inside a GeoJSON polygon set from the response.

    For a council with no FeatureServer to query, publishing its collection
    zones as a GeoJSON FeatureCollection embedded in a page or a script instead.
    The address is geocoded through the shared World GeocodeServer, the zone
    whose polygon contains that point is found, and its ``properties`` are
    returned as a single record: the same record shape an attribute query would
    have produced, so the rest of the pipeline does not care which it was. An
    address that lands in no zone is reported as a not-found on its argument.

    Args:
        extract: ``callable(response, source) -> dict | list`` returning the
            GeoJSON FeatureCollection (or a bare feature list) from the response
            body. Defaults to parsing the body as JSON. Supply one when the
            GeoJSON is embedded in a larger document.
        address: ``source.params`` field holding the address, or a callable
            resolved against ``**source.params`` (use one to append the state or
            country the geocoder needs).
    """

    def __init__(
        self,
        *,
        extract: Callable[[Response, BaseSource | None], Any] | None = None,
        address: str | Callable[..., str] = "address",
    ):
        self.extract = extract
        self.address = address

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        params = source.params if source is not None else {}
        query, field = _resolve_address(self.address, params)
        reported = params.get(field, query)
        try:
            location = geocode(query)
        except ArcGisError as e:
            raise SourceArgumentNotFound(field, reported) from e

        data = self.extract(response, source) if self.extract else response.json()
        features = data["features"] if isinstance(data, dict) else data
        for feature in features:
            ring = feature["geometry"]["coordinates"][0]
            if point_in_polygon(location["x"], location["y"], ring):
                return [feature["properties"]]
        raise SourceArgumentNotFound(field, reported)
