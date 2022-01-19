import json
from datetime import datetime
from datetime import timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Colchester.gov.uk"
DESCRIPTION = "Source for Colchester.gov.uk services for the borough of Colchester, UK."
URL = "https://colchester.gov.uk"
TEST_CASES = {
    "High Street, Colchester": {"llpgid": "1197e725-3c27-e711-80fa-5065f38b5681"},  # Should be 0
    "Church Road, Colchester": {"llpgid": "30213e07-6027-e711-80fa-5065f38b56d1"},
    "The Lane, Colchester": {"llpgid": "7cd96a3d-6027-e711-80fa-5065f38b56d1"},
}

ICONS = {
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
                        date = datetime.strptime(data["DatesOfFirstCollectionDays"][key], "%Y-%m-%dT%H:%M:%S")
                        if not weeks["WeekOne"]:
                            date = date + timedelta(days=7)
                        if date > datetime.now():
                            entries.append(
                                Collection(
                                    date=date.date(),
                                    t=day["Name"].title(),
                                    icon=ICONS[day["Name"]],
                                )
                            )
                        entries.append(
                            Collection(
                                date=date.date() + timedelta(days=14),
                                t=day["Name"].title(),
                                icon=ICONS[day["Name"]],
                            )
                        )
                    except ValueError:
                        pass  # ignore date conversion failure for not scheduled collections

        return entries
