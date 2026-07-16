import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Municipio de Ciudad de la Costa"
DESCRIPTION = "Source for household waste (general and recyclables) collection in Ciudad de la Costa, Canelones, Uruguay."
URL = "https://www.imcanelones.gub.uy"
COUNTRY = "uy"
TEST_CASES = {
    "De los Pinos, Lomas de Solymar": {"address": "De los Pinos, Ciudad de la Costa"},
    "Cuba, Parque de Carrasco": {"address": "1901 Cuba, Ciudad de la Costa"},
    "Guillermo Perez Butler, El Pinar": {
        "address": "1944 Avenida Guillermo Perez Butler, Ciudad de la Costa"
    },
}

ICON_MAP = {
    "General": Icons.GENERAL_WASTE,
    "Reciclables": Icons.RECYCLING,
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (or street name) within Ciudad de la Costa, e.g. 'De los Pinos, Ciudad de la Costa' or '1901 Cuba, Ciudad de la Costa'. Adding the neighbourhood (barrio) improves accuracy for common street names.",
    },
    "de": {
        "address": "Straßenadresse (oder nur der Straßenname) in Ciudad de la Costa, z. B. 'De los Pinos, Ciudad de la Costa'. Die Angabe des Stadtviertels (barrio) verbessert die Genauigkeit bei häufigen Straßennamen.",
    },
    "it": {
        "address": "Indirizzo (o solo il nome della via) a Ciudad de la Costa, ad es. 'De los Pinos, Ciudad de la Costa'. Aggiungere il quartiere (barrio) migliora la precisione per i nomi di via comuni.",
    },
    "fr": {
        "address": "Adresse (ou simplement le nom de la rue) à Ciudad de la Costa, par ex. 'De los Pinos, Ciudad de la Costa'. Ajouter le quartier (barrio) améliore la précision pour les noms de rue courants.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Address",
    },
    "de": {
        "address": "Adresse",
    },
    "it": {
        "address": "Indirizzo",
    },
    "fr": {
        "address": "Adresse",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address (house number and street, or just the street) within Ciudad de la Costa. "
    "The address is geocoded and matched against the municipality's published waste collection zone map "
    "(https://www.google.com/maps/d/u/0/viewer?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel). "
    "If your street name is common to multiple neighbourhoods, include the neighbourhood (barrio) name "
    "for a more accurate match.",
}

# Google MyMaps "MUNICIPIO DE CIUDAD DE LA COSTA" map, exported as KML.
# https://www.google.com/maps/d/u/0/viewer?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel
_KML_URL = (
    "https://www.google.com/maps/d/kml?mid=17F0VsWkN9V7hoqMSyQ_H2_rl0SYLlZel&forcekml=1"
)
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
_KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}

_WEEKDAY_MAP = {
    "LUNES": 0,
    "MARTES": 1,
    "MIERCOLES": 2,
    "JUEVES": 3,
    "VIERNES": 4,
    "SABADO": 5,
    "DOMINGO": 6,
}
_WEEKDAY_RE = re.compile("|".join(_WEEKDAY_MAP))


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test. polygon is a list of (lon, lat)."""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    xinters = p1x
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if min(p1y, p2y) < y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xinters:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


@dataclass
class _Zone:
    polygon: list[tuple[float, float]]
    mixed_days: set
    recycling_days: set


def _parse_zones() -> list[_Zone]:
    """Fetch and parse the 'RECOLECCIÓN DE RESIDUOS' zone polygons from the KML export.

    Each placemark name encodes the weekly collection days for mixed
    ("MEZCLADOS") and recyclable ("RECICLABLES") waste, e.g.:
        "MATUTINO: MEZCLADOS (MIÉRCOLES - DOMINGOS) RECICLABLES (MARTES)"
    """
    r = requests.get(_KML_URL, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    document = root.find("kml:Document", _KML_NS)
    if document is None:
        raise ValueError("Unexpected KML structure: missing Document element")

    zones: list[_Zone] = []
    for folder in document.findall("kml:Folder", _KML_NS):
        folder_name = folder.findtext("kml:name", default="", namespaces=_KML_NS)
        if "RESIDUOS" not in _strip_accents(folder_name).upper():
            continue

        for placemark in folder.findall("kml:Placemark", _KML_NS):
            raw_name = placemark.findtext("kml:name", default="", namespaces=_KML_NS)
            norm = (
                _strip_accents(re.sub(r"\s+", " ", raw_name.replace("\xa0", " ")))
                .strip()
                .upper()
            )

            mixed_m = re.search(r"MEZCLADOS\s*\(([^)]+)\)", norm)
            recycling_m = re.search(r"RECICLABLES\s*\(([^)]+)\)", norm)
            if not (mixed_m and recycling_m):
                continue

            mixed_days = {
                _WEEKDAY_MAP[d] for d in _WEEKDAY_RE.findall(mixed_m.group(1))
            }
            recycling_days = {
                _WEEKDAY_MAP[d] for d in _WEEKDAY_RE.findall(recycling_m.group(1))
            }
            if not mixed_days or not recycling_days:
                continue

            coords_text = placemark.findtext(
                "kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates",
                default="",
                namespaces=_KML_NS,
            )
            polygon: list[tuple[float, float]] = []
            for point in coords_text.split():
                lon_str, lat_str, *_rest = point.split(",")
                polygon.append((float(lon_str), float(lat_str)))
            if len(polygon) < 3:
                continue

            zones.append(
                _Zone(
                    polygon=polygon,
                    mixed_days=mixed_days,
                    recycling_days=recycling_days,
                )
            )
    return zones


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def _geocode(self) -> tuple[float, float]:
        """Resolve the address to (longitude, latitude) via Nominatim (OpenStreetMap)."""
        query = f"{self._address}, Ciudad de la Costa, Canelones, Uruguay"
        r = requests.get(
            _NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": "1",
                "countrycodes": "uy",
            },
            headers={"User-Agent": "hacs_waste_collection_schedule"},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise SourceArgumentNotFound("address", self._address)
        return float(results[0]["lon"]), float(results[0]["lat"])

    def fetch(self) -> list[Collection]:
        lon, lat = self._geocode()

        zones = _parse_zones()
        zone = next((z for z in zones if _point_in_polygon(lon, lat, z.polygon)), None)
        if zone is None:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition="the address was found but does not fall within any known "
                "collection zone, please check the spelling and try adding the neighbourhood name.",
            )

        entries: list[Collection] = []
        today = date.today()
        for offset in range(60):
            d = today + timedelta(days=offset)
            weekday = d.weekday()
            if weekday in zone.mixed_days:
                entries.append(
                    Collection(date=d, t="General", icon=ICON_MAP["General"])
                )
            if weekday in zone.recycling_days:
                entries.append(
                    Collection(date=d, t="Reciclables", icon=ICON_MAP["Reciclables"])
                )

        return entries
