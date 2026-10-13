"""GrandLyon calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import datetime
from typing import Any

from curl_cffi.requests import RequestsError

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

BAN_GEOCODE_URL = "https://api-adresse.data.gouv.fr/search/"
PHOTON_GEOCODE_URL = "https://download.data.grandlyon.com/geocoding/photon-bal/api"
WFS_URL = "https://data.grandlyon.com/geoserver/wfs"
WFS_TYPENAME = "gic_collecte.circuitcollecte"
SEARCH_RADIUS_DEG = 0.0015
DAY_COLUMNS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
}


def _retrieve(source: BaseSource) -> Any:
    lat, lon = _geocode(source, source.params["address"])
    bbox = (
        str(lon - SEARCH_RADIUS_DEG)
        + ","
        + str(lat - SEARCH_RADIUS_DEG)
        + ","
        + str(lon + SEARCH_RADIUS_DEG)
        + ","
        + str(lat + SEARCH_RADIUS_DEG)
    )
    resp = source.session.get(
        WFS_URL,
        params={
            "SERVICE": "WFS",
            "VERSION": "2.0.0",
            "REQUEST": "GetFeature",
            "typename": WFS_TYPENAME,
            "outputFormat": "application/json",
            "SRSNAME": "EPSG:4171",
            "BBOX": bbox + ",EPSG:4171",
            "count": "200",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return (resp, lat, lon)


def _parse(source: BaseSource, raw) -> list[dict[str, Any]]:
    resp, lat, lon = raw
    data = resp.json()
    features = data.get("features", [])
    if not features:
        raise SourceArgumentNotFound("address", source.params["address"])
    best_per_type: dict[str, tuple[float, set[int]]] = {}
    for feature in features:
        props = feature.get("properties", {})
        waste_type = props.get("typedechet")
        if not waste_type:
            continue
        days = set()
        for day_col, weekday_num in DAY_COLUMNS.items():
            val = props.get(day_col, "Non")
            if val and val != "Non":
                days.add(weekday_num)
        if not days:
            continue
        dist = _min_distance_to_feature(lat, lon, feature.get("geometry", {}))
        if waste_type not in best_per_type or dist < best_per_type[waste_type][0]:
            best_per_type[waste_type] = (dist, days)
    if not best_per_type:
        raise SourceArgumentNotFound("address", source.params["address"])
    now = datetime.date.today()
    entries = []
    for waste_type, (_, weekdays) in best_per_type.items():
        for year in (now.year, now.year + 1):
            d = datetime.date(year, 1, 1)
            end = datetime.date(year, 12, 31)
            while d <= end:
                if d.weekday() in weekdays:
                    entries.append({"date": d, "type": waste_type})
                d += datetime.timedelta(days=1)
    return entries


def _min_distance_to_feature(lat, lon, geometry):
    """Minimum squared distance from (lat, lon) to any vertex in geometry."""
    min_dist = float("inf")
    coords_list = geometry.get("coordinates", [])
    for line in coords_list:
        for point in line:
            dlat = lat - point[1]
            dlng = lon - point[0]
            dist = dlat * dlat + dlng * dlng
            if dist < min_dist:
                min_dist = dist
    return min_dist


def _geocode(source: BaseSource, address):
    """Geocode address via BAN then Photon fallback."""
    try:
        resp = source.session.get(
            BAN_GEOCODE_URL, params={"q": address, "limit": 1}, timeout=10
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            coords = features[0]["geometry"]["coordinates"]
            return (coords[1], coords[0])
    except (RequestsError, ValueError):
        pass
    try:
        resp = source.session.get(
            PHOTON_GEOCODE_URL, params={"q": address, "limit": 1}, timeout=10
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if features:
            coords = features[0]["geometry"]["coordinates"]
            return (coords[1], coords[0])
    except (RequestsError, ValueError):
        pass
    raise SourceArgumentNotFound("address", address)


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
