from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import json
from dateutil.parser import parse
from datetime import datetime

TITLE = "Whittlesea Council"
DESCRIPTION = "Source for Whittlesea Council (VIC) rubbish collection."
URL = "https://whittlesea.vic.gov.au/community-support/my-neighbourhood/"

TEST_CASES = {
    "Random address": {
        "street_number": "5",
        "street_name": "Hawkstowe Parade",
        "suburb": "South Morang",
        "postcode": "3752",
    },
    "Whittlesea Council Office": {
        "street_number": "25",
        "street_name": "Ferres Boulevard",
        "suburb": "South Morang",
        "postcode": "3752",
    }
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
    "content-type": "application/json",
}

NAMES = {
    "rubbish": "Red (rubbish)",
    "recycling": "Yellow (recycling)",
    "glass": "Purple (glass)",
    "green": "Green (garden)",
}

ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "glass": "mdi:glass-fragile",
    "green": "mdi:leaf",
}

# Only a year's worth of dates is available
WEEKS = 53

# Time to wait for initial connection, then response
TIMEOUT=(10,5)

class Source:
    def __init__(self, suburb, street_name, street_number, postcode):
        self.suburb = suburb
        self.street_name = street_name
        self.street_number = street_number
        self.postcode = postcode

    def fetch(self):
        # Retrieve geolocation for our address
        # (TODO: cache the LAT/LON results)
        address = self.street_number+" "+self.street_name+" "+self.suburb+" "+self.postcode
        PARAMS = {"address": address}
        url="https://www.whittlesea.vic.gov.au/umbraco/api/vicmap/GetAddressResultsUsingArcGis/"
        r = requests.get(
            url,
            headers=HEADERS,
            params=PARAMS,
            timeout=TIMEOUT,
        )

        # TODO: better error handling of parsing issues
        json_string = r.text.encode('raw_unicode_escape').decode('unicode_escape').lstrip('\"').rstrip('\"')
        data = json.loads(json_string)

        if not isinstance(data, dict):
            raise Exception("malformed response from web query")

        features=data.get("features")

        # Find the coordinates for our address
        # TODO: check that there is only one geometry
        geometry = features[0].get("geometry")
        geo_x = str(geometry.get("x"))
        geo_y = str(geometry.get("y"))

        # Armed with the LAT and LON coordinates, we construct
        # a request to fetch the waste pick-up schedules
        url="https://www.whittlesea.vic.gov.au/umbraco/api/cartomap/GetQueryResultsArcGisWasteCollection"

        firstQuery = "geometry%3D"+geo_x+","+geo_y+"%26geometryType%3DesriGeometryPoint%26inSR%3D4326%26spatialRel%3DesriSpatialRelIntersects%26outFields%3DName%26returnGeometry%3Dfalse%26f%3Djson"

        secondQuery = "where%3Dzonename%253D%2527%7B0%7D%2527%2Band%2Bdate%3ECURRENT_TIMESTAMP-1%26time%3D%26topFilter%3D%257B%250D%250A%2B%2B%2522groupByFields%2522%253A%2B%2522zonename%2522%252C%250D%250A%2B%2B%2522topCount%2522%253A%2B"+str(WEEKS)+"%252C%250D%250A%2B%2B%2522orderByFields%2522%253A%2B%2522date%2522%250D%250A%257D%26outFields%3D*%26orderByFields%3Ddate%26resultRecordCount%3D"+str(WEEKS)+"%26f%3Djson"

        url += "?firstQuery="+firstQuery+"&secondQuery="+secondQuery

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=(5,3),
        )

        json_string = r.text.encode('raw_unicode_escape').decode('unicode_escape').lstrip('\"').rstrip('\"')
        data = json.loads(json_string)

        entries = []

        today = datetime.utcnow().date()
        for item in data["rows"]:
            if "cartodb_id" in item:
              collection_date = parse(item["date"]).date()
              # Only return dates in the future
              if (collection_date - today).days >= 0:
                #print(f"found date {collection_date}")
                entries.append(Collection(date=collection_date,t=NAMES.get("rubbish"),icon=ICON_MAP.get("rubbish"),))
                if item["recycling"] == 1:
                    entries.append(Collection(date=collection_date,t=NAMES.get("recycling"),icon=ICON_MAP.get("recycling")))
                if item["green"] == 1:
                    entries.append(Collection(date=collection_date,t=NAMES.get("green"),icon=ICON_MAP.get("green")))
                if item["glass"] == 1:
                    entries.append(Collection(date=collection_date,t=NAMES.get("glass"),icon=ICON_MAP.get("glass")))

        return entries
