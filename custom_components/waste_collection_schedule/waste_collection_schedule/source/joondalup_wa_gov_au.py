import json
from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from requests.utils import requote_uri
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "City of Joondalup"
DESCRIPTION = "Source for City of Joondalup (WA) waste collection."
URL = "https://www.joondalup.wa.gov.au"
TEST_CASES = {
    "test address": {
        "number": "2",
        "street": "Ashburton Drive",
        "suburb": "Heathridge",
    },
    "test mapkey": {
        "mapkey": 785,
    },
}
HEADERS: dict = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}
DAYS: dict = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}
ICON_MAP: dict = {
    "Recycling": "mdi:recycle",
    "Bulk Put Out": "mdi:tree",
    "Bulk Pick Up": "mdi:tree",
    "General Waste": "mdi:trash-can",
    "Green Waste": "mdi:leaf",
}


# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        number=None,
        street=None,
        suburb=None,
        mapkey=None,
    ):
        if mapkey is None:
            self._number = str(number)
            self._street = str(street)
            self._suburb = str(suburb).upper()
            self._mapkey = None
        else:
            self._number = None
            self._street = None
            self._suburb = None
            self._mapkey = str(mapkey)

    def format_date(self, s: str) -> date:
        dt = datetime.strptime(s, "%A %d/%m/%Y").date()
        return dt

    def generate_general_waste_date(self, s: datetime, d: int) -> date:
        rr = rrule(WEEKLY, dtstart=s, byweekday=d)
        dt = rr.after(s)
        return dt.date()

    def generate_recycle_dates(self, s: str) -> tuple:
        d: date = self.format_date(s)
        dt1: date = d + timedelta(days=-7)
        dt2: date = d + timedelta(days=7)
        return dt1, dt2

    def fetch(self):
        start_date = datetime.now() + timedelta(days=-1)

        s = requests.Session()

        if self._mapkey is None:
            # use address details to find the mapkey
            search_term = requote_uri(f"{self._street} {self._suburb}")
            r = s.get(
                f"https://www.joondalup.wa.gov.au/aapi/coj/propertylookup/{search_term}",
                headers=HEADERS,
            )
            properties = json.loads(r.content)
            for property in properties:
                if str(property["house_no"]) == self._number:
                    self._mapkey = property["mapkey"]

        # use the mapkey to get the schedule
        r = s.get(
            f"https://www.joondalup.wa.gov.au/aapi/coj/bindatelookup/{self._mapkey}",
            headers=HEADERS,
        )
        pickups = json.loads(r.content)[0]

        # some waste types just state the collection day and frequency
        # so generate dates for those
        general = self.generate_general_waste_date(
            start_date, DAYS[pickups["Rubbish_Day"].upper().strip()]
        )
        recycle1, recycle2 = self.generate_recycle_dates(pickups["Next_Recycling_Date"])

        schedule: dict = {
            "Recycling": self.format_date(pickups["Next_Recycling_Date"]),
            "Bulk Put Out": self.format_date(pickups["Bulk_Rubbish_Put_Out"]),
            "Bulk Pick Up": self.format_date(pickups["Bulk_Rubbish_Pick_Up"]),
            "General Waste": general,
            "Green Waste": recycle1,
            "Green Waste ": recycle2,
        }

        entries = []

        for item in schedule:
            entries.append(
                Collection(
                    date=schedule[item],
                    t=item.strip(),
                    icon=ICON_MAP.get(item.strip()),
                )
            )

        return entries
