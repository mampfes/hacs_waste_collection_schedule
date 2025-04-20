import logging
from datetime import datetime
import urllib.parse
from typing import Dict, Any, List, Tuple
from shapely.geometry import Point, shape

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
GEOCODE_API_URL = "https://api.geocode.earth/v1/autocomplete"
GEOCODE_API_KEY = "ge-39bfbedc55be11c0"
ZONES_API_URL = "https://d2nozjvesbm579.cloudfront.net/ogr2ogr?source=data.gov.au/bendigo/cogb-garbage_collection_zones.shz"

# Test cases for validation
TEST_CASES = {
    "Bunnings Epsom": { 
        "street_address": "91-99 Midland Highway Epsom, VIC 3551"
    },
    "Bunnings Bendigo": {
        "street_address": "263-265 High Street Kangaroo Flat, VIC 3555"
    },
    "Alfa Kitchen Bendigo": {
        "street_address": "234 Hargreaves St, Bendigo VIC 3550"
    }
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
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        session = requests.Session()

        encoded_address = urllib.parse.quote(self._street_address)
        
        # Get the geocoded address coordinates
        response = session.get(
            f"{GEOCODE_API_URL}?text={encoded_address}&layers=address,street"
            f"&boundary.rect.min_lat={BENDIGO_BOUNDS['min_lat']}"
            f"&boundary.rect.min_lon={BENDIGO_BOUNDS['min_lon']}"
            f"&boundary.rect.max_lat={BENDIGO_BOUNDS['max_lat']}"
            f"&boundary.rect.max_lon={BENDIGO_BOUNDS['max_lon']}"
            f"&api_key={GEOCODE_API_KEY}",
        )
        response.raise_for_status()
        addressSearchApiResults = response.json()
        if (
            "features" not in addressSearchApiResults
            or not addressSearchApiResults["features"]
        ):
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Address not found in Bendigo area. Please check your address at https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night",
            )

        address_feature = addressSearchApiResults["features"][0]
        address_coords = address_feature["geometry"]["coordinates"]
        address_point = Point(address_coords)

        # Get the collection zones data (I had a quick look and it seems like the cloudfront FQDN should stay the same)
        response = session.get(ZONES_API_URL)
        response.raise_for_status()
        zones_data = response.json()

        # Find which zone contains the address point
        found_zone = None
        for feature in zones_data["features"]:
            zone_shape = shape(feature["geometry"])
            if zone_shape.contains(address_point):
                found_zone = feature
                break

        if not found_zone:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Address not found in any Bendigo collection zone. Please check your address at https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night",
            )

        _LOGGER.debug("Found collection zone: %s", found_zone["properties"]["name"])

        entries = []
        zone_props = found_zone["properties"]

        def add_collection(desc: str, day: str, weeks: int, start: str, collection_type: str):
            if not desc:
                raise ValueError(f"Missing description for {WASTE_NAMES[collection_type]} collection")
            
            if not start:
                raise ValueError(f"Missing start date for {WASTE_NAMES[collection_type]} collection")

            try:
                start_date = datetime.strptime(start, "%Y-%m-%d").date()
                entries.append(
                    Collection(
                        date=start_date,
                        t=WASTE_NAMES[collection_type],
                        icon=ICON_MAP[collection_type]
                    )
                )
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
