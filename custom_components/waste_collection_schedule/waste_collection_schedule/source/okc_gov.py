import json
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "City of Oklahoma City (unofficial)"
DESCRIPTION = "Source for okc.gov services for City of Oklahoma City"
URL = "https://www.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"objectID": "1781151"},
    "Test_002": {"objectID": "2002902"},
    "Test_003": {"objectID": 1935340},
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en,en-GB;q=0.7,en-US;q=0.3",
    "Upgrade-Insecure-Requests": "1",
}
ICON_MAP = {
    "TRASH": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "BULKY": "mdi:sofa",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "try_offical": "If checked, will attempt to use the official source at data.okc.gov. This probably fails as they now use scraping protection.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Using a browser, go to [data.okc.gov](https://data.okc.gov/portal/page/viewer?datasetName=Address%20Trash%20Services). "
    "Click on the `Map` tab, search for your address, then click on your house. Your schedule will be displayed. "
    "Click on the `Table` tab, then click on the `Filter By Map` menu item, and click `Apply` to reduce the number of items being displayed. Note: In the previous step, the more you zoom in on your house, the better this filter works. "
    "Find your address in the filtered list and make a note of the `Object ID` number in the first column. This is the number you need to use."
}


class Source:
    def __init__(self, objectID, try_offical=False):
        self._url = "https://okc.schizo.dev/trash"  # unofficial source
        if try_offical:
            self._url = "https://data.okc.gov/services/portal/api/data/records/Address%20Trash%20Services"

        self._recordID = str(objectID)

    def fetch(self):
        s = requests.Session()
        r = s.get(
            self._url,
            params={"recordID": self._recordID},
            headers=HEADERS,
        )

        try:
            json_data = json.loads(r.text)
        except Exception as e:
            raise Exception("Invalid response returned from data.okc.gov") from e
        else:
            waste_types = []
            # Build list of collection categories
            for item in json_data["Fields"][
                3:-1
            ]:  # limit to those entries containing collection info
                waste_types.append(item["FieldName"].replace("Next_", "").split("_")[0])
            # Build list of collection days/dates
            waste_dates = []
            action_day = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            for item in json_data["Records"][0][
                3:-1
            ]:  # limit to those entries containing collection info
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
