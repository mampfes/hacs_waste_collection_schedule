from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Merri-bek City Council"
DESCRIPTION = "Source for Merri-bek City Council (VIC) rubbish collection."
URL = "https://www.merri-bek.vic.gov.au"

TEST_CASES = {
    "Monday": {"address": "1 Vincent Street Oak Park 3046"},
    "Tuesday": {"address": "10 Gaffney Street Coburg North 3058"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "FOGO": "mdi:leaf",
}


class Source:
    def __init__(self, address):
        self.address = address

    def fetch(self):
        # Step 1: ArcGIS lookup to resolve address into coordinates & codes
        query_url = "https://services6.arcgis.com/8L5sOwfzTAvcvQur/ArcGIS/rest/services/WasteServices4Bin/FeatureServer/0/query"
        params = {
            "where": f"EZI_Address LIKE '{self.address}%'",
            "outFields": "EZI_Address,Waste_Rate_Code,Recycling_Rate_Code,FOGO_Rate_Code,Glass_Rate_Code,Day,Zone,GlassWeek",
            "returnGeometry": "true",
            "f": "json",
        }

        r = requests.get(query_url, params=params)
        r.raise_for_status()
        data = r.json()

        features = data.get("features")
        if not features:
            raise Exception("Address not found")

        attr = features[0]["attributes"]
        geom = features[0]["geometry"]

        # Step 2: Call Merri-bek's live AddressDetails API
        address_url = "https://www.merri-bek.vic.gov.au/api/AddressDetails"
        api_params = {
            "xPoint": geom["x"],
            "yPoint": geom["y"],
            "wasteDay": attr["Day"],
            "wasteRateCode": attr["Waste_Rate_Code"],
            "recycleRateCode": attr["Recycling_Rate_Code"],
            "fogoRateCode": attr["FOGO_Rate_Code"],
            "glassRateCode": attr["Glass_Rate_Code"],
            "zone": attr["Zone"],
            "glassWeekNumber": attr["GlassWeek"],
            "address": attr["EZI_Address"],
            "cpage": "86612",
        }

        r = requests.get(address_url, params=api_params)
        r.raise_for_status()
        data = r.json()

        if not data or len(data) == 0:
            raise Exception("No collection data found")

        # Step 3: Convert API response into schedule entries
        schedule = data[0]  # first result contains the collections

        entries = []

        # Map Merri-bek keys to waste types
        mapping = {
            "allBinDays": "Rubbish",
            "allRecycleDays": "Recycling",
            "allFogoDays": "FOGO",
            "allGlassDays": "Glass",
        }

        for api_key, bin_type in mapping.items():
            if api_key not in schedule:
                continue
            for d in schedule[api_key]:
                try:
                    date_obj = datetime.strptime(d, "%d-%m-%Y").date()
                except ValueError:
                    continue

                # Prevent duplicate dates for same bin type
                if any(c.date == date_obj and c.type == bin_type for c in entries):
                    continue

                entries.append(
                    Collection(
                        date=date_obj,
                        t=bin_type,
                        icon=ICON_MAP.get(bin_type),
                    )
                )

        return entries
