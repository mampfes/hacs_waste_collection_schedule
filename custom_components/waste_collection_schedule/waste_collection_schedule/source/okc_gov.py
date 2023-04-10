import json
import requests

from datetime import datetime, timedelta
from waste_collection_schedule import Collection

TITLE = "City of Oklahoma City"
DESCRIPTION = (
    "Source for okc.gov services for City of Oklahoma City"
)
URL = "https://www.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"objectID": "1781151"},
    "Test_002": {"objectID": "2002902"},
    "Test_003": {"objectID": "1935340"},
}
HEADERS = {
"content-type": "text/json",
"user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0",
}
ICON_MAP = {
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:sofa",
}


class Source:
    def __init__(self, objectID):
        self._recordID = str(objectID)

    def fetch(self):

        s = requests.Session()
        r = s.get(
            f"https://data.okc.gov/services/portal/api/data/records/Address%20Trash%20Services?recordID={self._recordID}",
            headers=HEADERS,
        )

        try:
            json_data = json.loads(r.text)
        except Exception as e:
            raise Exception("invalid response returned from data.okc.gov") from e
        else:
            waste_types = []
            # Build list of collection categories
            for item in json_data["Fields"][3:-1]:  # limit to those entries containing collection info
                waste_types.append(item["FieldName"].replace("Next_", "").split("_")[0])
            # Build list of collection days/dates
            waste_dates = []
            action_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            for item in json_data["Records"][0][3:-1]:# limit to those entries containing collection info
                if item != "Not Available":  # ignore missing collections
                    if "day" in item:  # convert day of week into next collection date
                        while action_day.strftime("%A") != item:
                            action_day += timedelta(days=+1)
                        waste_dates.append(action_day.date())
                    else:
                        waste_dates.append(datetime.strptime(item, "%b %d, %Y").date())
            schedule = list(zip(waste_types, waste_dates))

            entries = []
            for waste in schedule:
                entries.append(
                    Collection(
                        date=waste[1],
                        t=waste[0],
                        icon=ICON_MAP.get(waste[0].upper()),
                    )
                )            

        return entries


        # # api response can be inconsistent, so catch cases were it doesn't return a collection schedule
        ## try:
        ##     json_data = json.loads(r.text)
        
        # try:
        #     json_data = json.loads(r.text)
        # except Exception as e:
        #     raise Exception("Invalid response returned from data.okc.gov") from e
        ## except:
        ##     print("JSON Decode Error - invalid response returned from data.okc.gov")
        # else:
        #     # Build list of collection categories
        #     waste_types = []
        #     for item in json_data["Fields"][3:-1]:  # limit to those entries containing collection info
        #         waste_types.append(item["FieldName"].replace("Next_", "").split("_")[0])
        #     # Build list of collection days/dates
        #     waste_dates = []
        #     action_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        #     for item in json_data["Records"][0][3:-1]:# limit to those entries containing collection info
        #         if item != "Not Available":  # ignore missing collections
        #             if "day" in item:  # convert day of week into next collection date
        #                 while action_day.strftime("%A") != item:
        #                     action_day += timedelta(days=+1)
        #                 waste_dates.append(action_day.date())
        #             else:
        #                 waste_dates.append(datetime.strptime(item, "%b %d, %Y").date())
        #     schedule = list(zip(waste_types, waste_dates))

        #     entries = []
        #     for waste in schedule:
        #         entries.append(
        #             Collection(
        #                 date=waste[1],
        #                 t=waste[0],
        #                 icon=ICON_MAP.get(waste[0].upper()),
        #             )
        #         )            

        # return entries
