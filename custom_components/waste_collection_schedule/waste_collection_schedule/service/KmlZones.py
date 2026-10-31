"""Match a geocoded point to a published KML collection-zone polygon."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser, XmlParser
from waste_collection_schedule.service.ArcGis import point_in_polygon

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_NS = {"k": "http://www.opengis.net/kml/2.2"}


def normalise(value: str) -> str:
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", value)
            if not unicodedata.combining(c)
        )
        .upper()
        .split()
    )


class KmlWeekdayZoneParser(Parser[list[dict[str, Any]]]):
    """Read named weekday groups from the first polygon covering the address.

    Responses are the Nominatim point lookup and the KML document, in that
    order. ``groups`` maps type keys to regexes capturing the published days;
    ``weekdays`` maps the provider's normalised weekday names to Python indices.
    No collection weekday is supplied by the parser itself.
    """

    def __init__(
        self, *, folder: str, groups: Mapping[str, str], weekdays: Mapping[str, int]
    ):
        self.folder = re.compile(folder)
        self.groups = {key: re.compile(pattern) for key, pattern in groups.items()}
        self.weekdays = dict(weekdays)
        self.day_pattern = re.compile("|".join(map(re.escape, self.weekdays)))

    def __call__(
        self, responses: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if len(responses) != 2:
            raise ValueError("KML zone lookup needs a point and a map response")
        points = responses[0].json()
        address = str(source.params.get("address", "")) if source else ""
        if not points:
            raise SourceArgumentNotFound("address", address)
        x, y = float(points[0]["lon"]), float(points[0]["lat"])
        root = XmlParser()(responses[1], source)[0]
        document = root.find("k:Document", _NS)
        if document is None:
            raise ValueError("KML has no Document element")
        valid_zones = 0
        for folder in document.findall("k:Folder", _NS):
            if not self.folder.search(normalise(folder.findtext("k:name", "", _NS))):
                continue
            for place in folder.findall("k:Placemark", _NS):
                name = normalise(place.findtext("k:name", "", _NS))
                matches = {
                    key: pattern.search(name) for key, pattern in self.groups.items()
                }
                if not all(matches.values()):
                    continue
                days = {
                    key: {
                        self.weekdays[day]
                        for day in self.day_pattern.findall(match.group(1))
                    }
                    for key, match in matches.items()
                    if match is not None
                }
                if not all(days.values()):
                    continue
                coordinates = place.findtext(
                    "k:Polygon/k:outerBoundaryIs/k:LinearRing/k:coordinates", "", _NS
                )
                ring = [
                    [float(n) for n in point.split(",")[:2]]
                    for point in coordinates.split()
                ]
                if len(ring) < 3:
                    continue
                valid_zones += 1
                if point_in_polygon(x, y, ring):
                    return [
                        {"weekday": day, "type": key}
                        for key, values in days.items()
                        for day in sorted(values)
                    ]
        if not valid_zones:
            raise ValueError("KML carries no recognised collection zones")
        raise SourceArgumentNotFound(
            "address",
            address,
            message_addition="the address is outside the published collection zones; include the neighbourhood name.",
        )
