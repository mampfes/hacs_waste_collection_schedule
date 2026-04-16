import datetime

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "Métropole de Lyon"
DESCRIPTION = "Source script for data.grandlyon.com waste collection schedules"
URL = "https://data.grandlyon.com"
COUNTRY = "fr"

TEST_CASES = {
    "Oullins centre": {"address": "1 place Roger Salengro, Oullins"},
    "Lyon 3e Garibaldi": {"address": "208 rue Garibaldi, Lyon 3e"},
    "Villeurbanne Gratte-Ciel": {
        "address": "18 rue Francis de Pressensé, Villeurbanne"
    },
}

ICON_MAP = {
    "Ordures Ménagères": "mdi:trash-can",
    "Collecte Sélective": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including the city name (e.g. '1 place Roger Salengro, Oullins').",
    "fr": "Entrez votre adresse complète avec le nom de la commune (ex : '1 place Roger Salengro, Oullins').",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Your street address with city",
    },
    "fr": {
        "address": "Votre adresse postale avec la commune",
    },
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
    "fr": {"address": "Adresse"},
}

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


class Source:
    def __init__(self, address):
        normalized = address.strip() if isinstance(address, str) else address
        if not normalized:
            raise SourceArgumentRequired("address", "An address is required")
        self._address = normalized

    def fetch(self):
        lat, lon = self._geocode(self._address)

        bbox = (
            str(lon - SEARCH_RADIUS_DEG)
            + ","
            + str(lat - SEARCH_RADIUS_DEG)
            + ","
            + str(lon + SEARCH_RADIUS_DEG)
            + ","
            + str(lat + SEARCH_RADIUS_DEG)
        )
        resp = requests.get(
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
        data = resp.json()

        features = data.get("features", [])
        if not features:
            raise SourceArgumentNotFound("address", self._address)

        # For each waste type, keep only the CLOSEST circuit
        # to avoid merging days from neighbouring streets
        best_per_type = {}

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

            dist = self._min_distance_to_feature(lat, lon, feature.get("geometry", {}))

            if waste_type not in best_per_type or dist < best_per_type[waste_type][0]:
                best_per_type[waste_type] = (dist, days)

        if not best_per_type:
            raise SourceArgumentNotFound("address", self._address)

        # Generate ALL dates (framework handles filtering)
        now = datetime.date.today()
        entries = []

        for waste_type, (_, weekdays) in best_per_type.items():
            for year in (now.year, now.year + 1):
                d = datetime.date(year, 1, 1)
                end = datetime.date(year, 12, 31)
                while d <= end:
                    if d.weekday() in weekdays:
                        entries.append(
                            Collection(
                                date=d,
                                t=waste_type,
                                icon=ICON_MAP.get(waste_type),
                            )
                        )
                    d += datetime.timedelta(days=1)

        return entries

    @staticmethod
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

    @staticmethod
    def _geocode(address):
        """Geocode address via BAN then Photon fallback."""
        try:
            resp = requests.get(
                BAN_GEOCODE_URL,
                params={"q": address, "limit": 1},
                timeout=10,
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                return (coords[1], coords[0])
        except Exception:
            pass

        try:
            resp = requests.get(
                PHOTON_GEOCODE_URL,
                params={"q": address, "limit": 1},
                timeout=10,
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if features:
                coords = features[0]["geometry"]["coordinates"]
                return (coords[1], coords[0])
        except Exception:
            pass

        raise SourceArgumentNotFound("address", address)
