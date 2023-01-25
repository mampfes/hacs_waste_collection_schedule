import json
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Colchester City Council"
DESCRIPTION = "Source for Colchester.gov.uk services for the borough of Colchester, UK."
URL = "https://colchester.gov.uk"
TEST_CASES = {
    # "High Street, Colchester": {"llpgid": "1197e725-3c27-e711-80fa-5065f38b5681"},  # Should be 0
    "Church Road, Colchester": {"llpgid": "30213e07-6027-e711-80fa-5065f38b56d1"},
    "The Lane, Colchester": {"llpgid": "7cd96a3d-6027-e711-80fa-5065f38b56d1"},
}

ICON_MAP = {
    "Black bags": "mdi:trash-can",
    "Glass": "mdi:glass-fragile",
    "Cans": "mdi:trash-can",
    "Textiles": "mdi:hanger",
    "Paper/card": "mdi:recycle",
    "Plastics": "mdi:recycle",
    "Garden waste": "mdi:leaf",
    "Food waste": "mdi:food",
}


class Source:
    def __init__(self, llpgid):
        self._llpgid = llpgid

    def fetch(self):
        # get json file
        r = requests.get(
            f"https://new-llpg-app.azurewebsites.net/api/calendar/{self._llpgid}"
        )

        # extract data from json
        data = json.loads(r.text)

        entries = []

        for weeks in data["Weeks"]:
            rows = weeks["Rows"]
            for key in iter(rows):
                for day in rows[key]:
                    try:
                        # Colchester.gov.uk provide their rubbish collection information in the format of a 2-week
                        # cycle. These weeks represent 'Blue' weeks and 'Green' weeks (Traditionally, non-recyclables
                        # and recyclable weeks). The way the JSON response represents this is by specifying the
                        # `DatesOfFirstCollectionDays`, the first collection day of the cycle, and having a boolean
                        # `WeekOne` field in each week representing if it's the first week of the cycle, a 'Blue' week,
                        # or the second, a 'Green' week. If the week is not `WeekOne`, a 'Blue' week,  then 7 days need
                        # to be added to the `DatesOfFirstCollectionDays` date to provide the correct 'Green' week
                        # collection date.
                        date = datetime.strptime(
                            data["DatesOfFirstCollectionDays"][key], "%Y-%m-%dT%H:%M:%S"
                        )
                        if not weeks["WeekOne"]:
                            date = date + timedelta(days=7)
                        if date > datetime.now():
                            entries.append(
                                Collection(
                                    date=date.date(),
                                    t=day["Name"].title(),
                                    icon=ICON_MAP.get(day["Name"]),
                                )
                            )
                        # As Colchester.gov.uk only provides the current collection cycle, the next must be extrapolated
                        # from the current week. This is the same method the website uses to display further collection
                        # weeks.
                        entries.append(
                            Collection(
                                date=date.date() + timedelta(days=14),
                                t=day["Name"].title(),
                                icon=ICON_MAP.get(day["Name"]),
                            )
                        )
                    except ValueError:
                        pass  # ignore date conversion failure for not scheduled collections

        return entries
