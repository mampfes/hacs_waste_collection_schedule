import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Greater Bendigo"
DESCRIPTION = "Source for City of Greater Bendigo rubbish collection."
URL = "https://www.bendigo.vic.gov.au"

# Geographic boundaries for Bendigo area
BENDIGO_BOUNDS = {
    "min_lat": -37.07,
    "min_lon": 144.03,
    "max_lat": -36.39,
    "max_lon": 144.86
}

# API endpoints
ZONES_API_URL = "https://d2nozjvesbm579.cloudfront.net/ogr2ogr?source=data.gov.au/bendigo/cogb-garbage_collection_zones.shz"

# Test cases for validation
TEST_CASES = {
    "Bunnings Epsom": { 
        "latitude": -36.701755710607394,
        "longitude": 144.31310883736967
    },
    "Bunnings Bendigo": {
        "latitude": -36.808262837180514,
        "longitude": 144.24269331664098
    },
    "Alfa Kitchen Bendigo": {
        "latitude": -36.758540554036315, 
        "longitude": 144.2818129235716
    },
    # "Boundary Test - Friday Calendar B": {
    #     # Point exactly halfway between [144.2876297, -36.7616511] and [144.2855719, -36.7598316]
    #     "latitude": -36.76074135,  # (-36.7616511 + -36.7598316) / 2
    #     "longitude": 144.2866008   # (144.2876297 + 144.2855719) / 2
    # }
}

_LOGGER = logging.getLogger(__name__)

WASTE_NAMES = {
    "waste": "General Waste",
    "recycle": "Recycling",
    "green": "Green Waste"
}

ICON_MAP = {
    "waste": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "green": "mdi:leaf"
}


class Source:
    def __init__(self, latitude: float, longitude: float):
        """Initialize source with latitude and longitude coordinates.
        
        Args:
            latitude: Latitude coordinate (-37.07 to -36.39)
            longitude: Longitude coordinate (144.03 to 144.86)
        """
        if not BENDIGO_BOUNDS["min_lat"] <= latitude <= BENDIGO_BOUNDS["max_lat"]:
            raise SourceArgumentNotFound(
                "latitude",
                str(latitude),
                f"Latitude must be between {BENDIGO_BOUNDS['min_lat']} and {BENDIGO_BOUNDS['max_lat']}"
            )
        if not BENDIGO_BOUNDS["min_lon"] <= longitude <= BENDIGO_BOUNDS["max_lon"]:
            raise SourceArgumentNotFound(
                "longitude",
                str(longitude),
                f"Longitude must be between {BENDIGO_BOUNDS['min_lon']} and {BENDIGO_BOUNDS['max_lon']}"
            )
        
        self._latitude = latitude
        self._longitude = longitude

    def fetch(self):
        session = requests.Session()

        address_point = Point(self._longitude, self._latitude)
        
        response = session.get(ZONES_API_URL)
        response.raise_for_status()
        zones_data = response.json()

        def is_point_in_polygon(point, geometry):
            lat, lon = point
            
            # Extract coordinates from GeoJSON geometry
            if geometry["type"] == "Polygon":
                # For Polygon, coordinates are an array of linear rings
                # The first ring is the exterior ring
                polygon = [(coord[1], coord[0]) for coord in geometry["coordinates"][0]]
                return _check_point_in_polygon((lat, lon), polygon)
            elif geometry["type"] == "MultiPolygon":
                # For MultiPolygon, coordinates are an array of polygons
                # Check each polygon
                for i, polygon_coords in enumerate(geometry["coordinates"]):
                    polygon = [(coord[1], coord[0]) for coord in polygon_coords[0]]
                    if _check_point_in_polygon((lat, lon), polygon):
                        _LOGGER.debug("Point found in polygon %d", i)
                        return True
                return False
            else:
                raise ValueError(f"Unsupported geometry type: {geometry['type']}")

        def _check_point_in_polygon(point, polygon):
            lat, lon = point
            n = len(polygon)
            inside = False

            # Small epsilon value for floating point comparisons
            EPSILON = 1e-10

            # Close the polygon if not already closed
            if polygon[0] != polygon[-1]:
                polygon = polygon + [polygon[0]]

            for i in range(n):
                j = (i + 1) % n
                lat_i, lon_i = polygon[i]
                lat_j, lon_j = polygon[j]

                # Check if point is on or near the edge
                if abs((lon_j - lon_i) * (lat - lat_i) - (lat_j - lat_i) * (lon - lon_i)) < EPSILON:
                    # Point is on the line, now check if it's within the segment
                    if (min(lon_i, lon_j) - EPSILON <= lon <= max(lon_i, lon_j) + EPSILON and
                        min(lat_i, lat_j) - EPSILON <= lat <= max(lat_i, lat_j) + EPSILON):
                        return True 

                if ((lon_i > lon) != (lon_j > lon)):
                    intersect = (lon - lon_i) * (lat_j - lat_i) / (lon_j - lon_i) + lat_i
                    if lat <= intersect:
                        inside = not inside

            return inside

        # Find which zone contains the address point
        found_zones = []
        for feature in zones_data["features"]:
            zone_name = feature["properties"]["name"]
            if is_point_in_polygon((self._latitude, self._longitude), feature["geometry"]):
                _LOGGER.debug("Point found in zone: %s", zone_name)
                found_zones.append(feature)

        if not found_zones:
            raise SourceArgumentNotFound(
                "coordinates",
                f"({self._latitude}, {self._longitude})",
                "Coordinates not found in any Bendigo collection zone. Please check your location at https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night",
            )
        
        if len(found_zones) > 1:
            zone_names = [zone["properties"]["name"] for zone in found_zones]
            _LOGGER.debug("Point found in multiple zones: %s", zone_names)
            raise SourceArgumentNotFound(
                "coordinates",
                f"({self._latitude}, {self._longitude})",
                f"Coordinates are on a boundary between multiple zones: {', '.join(zone_names)}. "
                "To resolve this, please try adjusting your coordinates slightly (by 0.0001 degrees or less) "
                "in any direction. You can verify your zone at "
                "https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night"
            )

        found_zone = found_zones[0]
        _LOGGER.debug("Found collection zone: %s", found_zone["properties"]["name"])

        entries = []
        zone_props = found_zone["properties"]
        
        def add_collection(desc: str, day: str, weeks: int, start: str, collection_type: str):
            if not desc:
                raise ValueError(f"Missing description for {WASTE_NAMES[collection_type]} collection")
            
            if not start:
                raise ValueError(f"Missing start date for {WASTE_NAMES[collection_type]} collection")
            
            if not day:
                raise ValueError(f"Missing collection day for {WASTE_NAMES[collection_type]} collection")
            
            if not weeks or weeks < 1:
                raise ValueError(f"Invalid collection frequency for {WASTE_NAMES[collection_type]} collection")

            try:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
                
                start_day = start_date.strftime("%A")
                
                # If the start date isn't on the specified day, find the next occurrence
                if start_day != day:
                    days_ahead = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day) - \
                                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(start_day)
                    if days_ahead <= 0:
                        days_ahead += 7
                    start_date = start_date + timedelta(days=days_ahead)

                current_date = start_date
                end_date = datetime.now().date() + timedelta(days=365)
                
                while current_date <= end_date:
                    entries.append(
                        Collection(
                            date=current_date,
                            t=WASTE_NAMES[collection_type],
                            icon=ICON_MAP[collection_type]
                        )
                    )

                    current_date = current_date + timedelta(weeks=weeks)

            except ValueError as e:
                raise ValueError(f"Invalid date format for {WASTE_NAMES[collection_type]} collection: {start}") from e

        add_collection(
            zone_props.get("rub_desc"), 
            zone_props.get("rub_day"),
            zone_props.get("rub_weeks", 0),
            zone_props.get("rub_start"),
            "waste"
        )
        
        add_collection(
            zone_props.get("rec_desc"),
            zone_props.get("rec_day"),
            zone_props.get("rec_weeks", 0),
            zone_props.get("rec_start"),
            "recycle"
        )
        
        add_collection(
            zone_props.get("grn_desc"),
            zone_props.get("grn_day"),
            zone_props.get("grn_weeks", 0),
            zone_props.get("grn_start"),
            "green"
        )

        _LOGGER.debug("Entries: %s", entries)

        return entries
