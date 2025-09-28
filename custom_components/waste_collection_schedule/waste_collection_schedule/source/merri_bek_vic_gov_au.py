from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Merri-bek City Council"
DESCRIPTION = "Source for Merri-bek City Council (VIC) rubbish collection."
URL = "https://www.merri-bek.vic.gov.au"

TEST_CASES = {
    "Monday": {"address": "1 Widford Street Glenroy 3046"},
    "Tuesday": {"address": "1 Gaffney Street Coburg 3058"},
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Glass": "mdi:glass-fragile",
    "Green": "mdi:leaf",
}

COLLECTIONS = {
    "allBinDays": ["Rubbish", "Green"],
    "allGlassDays": ["Glass"],
    "allRecycleDays": ["Recycling"],
}


class Source:
    def __init__(self, address):
        self.address = address

    def fetch(self):
        # Step 1 – search for address and get geometry + attributes
        search_url = "https://services6.arcgis.com/8L5sOwfzTAvcvQur/ArcGIS/rest/services/WasteServices4Bin/FeatureServer/0/query"
        search_params = {
            "where": f"EZI_Address LIKE '{self.address}%'",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
        }
        r = requests.get(search_url, params=search_params)
        r.raise_for_status()

        data = r.json()
        features = data.get("features")
        if not features:
            raise Exception("Address not found")

        attributes = features[0]["attributes"]

        # ✅ The new API now includes bin dates directly in the attributes
        entries = []

        for field, waste_names in COLLECTIONS.items():
            if field in attributes and attributes[field]:
                # attributes[field] is a comma-separated list of dates like "02-10-2025,16-10-2025"
                dates = [d.strip() for d in attributes[field].split(",") if d.strip()]
                for collection_date in dates:
                    for waste_name in waste_names:
                        try:
                            entries.append(
                                Collection(
                                    date=datetime.strptime(collection_date, "%d-%m-%Y").date(),
                                    t=waste_name,
                                    icon=ICON_MAP.get(waste_name),
                                )
                            )
                        except ValueError:
                            # skip invalid dates
                            continue

        return entries
