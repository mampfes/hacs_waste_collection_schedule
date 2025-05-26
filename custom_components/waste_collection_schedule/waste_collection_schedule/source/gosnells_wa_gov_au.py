from datetime import datetime

import requests
from dateutil.rrule import DAILY, FR, MO, SA, SU, TH, TU, WE, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Gosnells"
DESCRIPTION = "Source for City of Gosnells, Western Australia."
URL = "https://www.gosnells.wa.gov.au/"
TEST_CASES = {
    "Test_001": {"address": "15 Mackay Crescent GOSNELLS 6110"},
    "Test_002": {"address": "7 Darkin Drive GOSNELLS 6110"},
    "Test_003": {"address": "35 Prince Street GOSNELLS 6110"},
}
HEADERS = {"user-agent": "Mozilla/5.0", "accept": "application/json"}
ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "recycling": "mdi:recycle",
    "green": "mdi:sprout",
    "junk": "mdi:television-classic",
}
DAYS = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}


class Source:
    def __init__(self, address):
        self._address = address

    def fetch(self):
        s = requests.Session()

        # get property id
        data = {"query": self._address}
        r = s.post(
            "https://t1.gosnells.wa.gov.au/API/waste/v8/address",
            headers=HEADERS,
            data=data,
        ).json()
        property_id = r["results"][0]["property_no"]

        # get schedule
        r = s.get(
            f"https://t1.gosnells.wa.gov.au/API/waste/v8/propertyNum/{property_id}",
            headers=HEADERS,
        ).json()

        entries = []
        for item in r["results"][0]:
            for waste_type in ICON_MAP:
                if waste_type in item and "status" not in item:
                    if waste_type == "rubbish":
                        # generate date from collection day
                        today = datetime.now()
                        day = DAYS[r["results"][0][item]]
                        dt = (rrule(DAILY, byweekday=day, dtstart=today)[0]).date()
                    else:
                        dt = datetime.strptime(r["results"][0][item], "%Y-%m-%d").date()
                    entries.append(
                        Collection(
                            date=dt,
                            t=waste_type.capitalize(),
                            icon=ICON_MAP.get(waste_type),
                        )
                    )

        return entries
