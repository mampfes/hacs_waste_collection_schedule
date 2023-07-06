import json
from datetime import date, timedelta
import urllib.parse

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Logan City Council"
DESCRIPTION = "Source for Logan City Council rubbish collection."
URL = "https://www.logan.qld.gov.au"
TEST_CASES = {
    "LCC ADMINISTRATION CENTRE": {
        "property_location": "LCC ADMINISTRATION CENTRE, 150 Wembley Road, LOGAN CENTRAL QLD 4114",
    },
    "The Family Place": {
        "property_location": "35 North Road, WOODRIDGE QLD 4114",
    },
    "Lee Naki's Takeaway": {
        "property_location": "2 Ashton Street, KINGSTON QLD 4114",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}

API_URL = "https://services5.arcgis.com/ZUCWDRj8F77Xo351/arcgis/rest/services/Logan_City_Bin_Collection/FeatureServer/0/query"

class Source:
    def __init__(self, property_location):
        self.property_location = urllib.parse.quote_plus(property_location)

    def fetch(self):

        # Retrieve collection day and whether there is recycling or green waste bin
        r = requests.get(f"{API_URL}?where=%20(Formatted_Property_Address%20%3D%20'{self.property_location}')%20&outFields=Collection_Day,Recycling_Week,Green_Waste_Week&outSR=4326&f=json",headers=HEADERS)
        data = json.loads(r.text)

        if data["features"] == []:
            return []

        collection_day = data["features"][0]["attributes"]["Collection_Day"]
        recycling_week = data["features"][0]["attributes"]["Recycling_Week"]
        green_waste_week = data["features"][0]["attributes"]["Green_Waste_Week"]

        today = date.today()
        entries = []

        if collection_day == 'MON':
            weekday = 0
        elif collection_day == 'TUE':
            weekday = 1
        elif collection_day == 'WED':
            weekday = 2
        elif collection_day == 'THU':
            weekday = 3
        elif collection_day == 'FRI':
            weekday = 4
        elif collection_day == 'SAT':
            weekday = 5
        elif collection_day == 'SUN':
            weekday = 6
        else:
            return []
        
        next_collection_date = today + timedelta((weekday - today.weekday() + 7 )% 7)
        
        # Add next 52 collection days
        for x in range(52):
            collection_date = next_collection_date+timedelta(weeks=x)
            week = collection_date.isocalendar().week % 2

            entries.append(
                Collection(
                    date=collection_date, t="Rubbish", icon="mdi:trash-can"
                )
            )

            # Check if Recycling Bin Collected
            if recycling_week != '':
                # Check if Recycling Week
                if (recycling_week == 'Week 1' and week == 1) or (recycling_week == 'Week 2' and week == 0):
                    entries.append(
                        Collection(
                            date=collection_date, t="Recycling", icon="mdi:recycle"
                        )
                    )

            # Check if Green Waste Bin Collected
            if green_waste_week != None:
                # Check if Green Waste Week
                if (green_waste_week == 'Week 1' and week == 1) or (green_waste_week == 'Week 2' and week == 0):
                    entries.append(
                        Collection(
                            date=collection_date, t="Green Waste", icon="mdi:leaf"
                        )
                    )

        return entries