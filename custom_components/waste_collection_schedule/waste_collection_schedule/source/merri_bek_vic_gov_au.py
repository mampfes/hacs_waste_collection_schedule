from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Merri-bek City Council"
DESCRIPTION = "Source for Merri-bek City Council (VIC) rubbish collection."
URL = "https://www.merri-bek.vic.gov.au"

TEST_CASES = {
    "Monday": {
        "address": "1 Widford Street Glenroy 3046",
    },
    "Tuesday": {
        "address": "1 Gaffney Street Coburg 3058",
    },
    "Wednesday": {
        "address": "1 Shorts Road Coburg North 3058",
    },
    "Thursday": {
        "address": "1 Glenroy Road Glenroy 3046",
    },
    "Friday": {
        "address": "1 Major Road Fawkner 3060",
    },
    "Glass Drop Off": {
        "address": "1 Elesbury Avenue Brunswick East 3057",
    },
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Green": "mdi:leaf",
}

COLLECTIONS = {
    "AllBinDays": ["Rubbish", "Green"],
    "AllGlassDays": ["Glass"],
    "AllRecycleDays": ["Recycling"],
}


class Source:
    def __init__(self, address):
        self.address = address

    def fetch(self):
        PARAMS = {
            "where": f"EZI_Address LIKE '{self.address}%'",
            "outFields": "EZI_Address,Waste_Rate_Code,Recycling_Rate_Code,FOGO_Rate_Code,Glass_Rate_Code,Day,Zone,GlassWeek",
            "returnGeometry": "true",
            "f": "json",
        }
        url = "https://services6.arcgis.com/8L5sOwfzTAvcvQur/ArcGIS/rest/services/WasteServices4Bin/FeatureServer/0/query/"
        r = requests.get(
            url,
            params=PARAMS,
        )
        r.raise_for_status()

        data = r.json()
        features = data.get("features")
        if not features:
            raise Exception("address not found")

        attributes = features[0]["attributes"]

        PARAMS = {
            "wasteDay": attributes["Day"],
            "wasteRateCode": attributes["Waste_Rate_Code"],
            "recycleRateCode": attributes["Recycling_Rate_Code"],
            "fogoRateCode": attributes["FOGO_Rate_Code"],
            "glassRateCode": attributes["Glass_Rate_Code"],
            "zone": attributes["Zone"],
            "glassWeekNumber": attributes["GlassWeek"],
            "address": attributes["EZI_Address"],
            "cpage": "94106",
        }
        url = "https://www.merri-bek.vic.gov.au/gis/AddressDetails.svc/fourbins/"
        r = requests.get(
            url,
            params=PARAMS,
        )
        r.raise_for_status()

        data = r.json()[0]

        entries = [
            Collection(
                date=datetime.strptime(collection_date, "%d-%m-%Y").date(),
                t=waste_name,
                icon=ICON_MAP.get(waste_name),
            )
            for collection_name, waste_names in COLLECTIONS.items()
            if collection_name in data
            for collection_date in data[collection_name]
            for waste_name in waste_names
        ]

        return entries
