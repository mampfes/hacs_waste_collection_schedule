from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection

TITLE = "Odense Renovation"
DESCRIPTION = "Source for Odense Renovation"
URL = "https://odenserenovation.dk"
TEST_CASES = {
    "Jernbanegade 19, Odense C": {"address_no": 122518},
    "Nyborgvej 3, Odense C": {"address_no": 133517},
    "Næsbyhave 105, Odense N": {"address_no": 134008},
}

API_URL = "https://mit.odenserenovation.dk/api/Calendar/GetCalendarByAddress"
ICON_MAP = {
    "00": "mdi:trash-can",  # Mad- og restaffald
    "10": "mdi:archive",  # Glas & metal og papir & småt pap
    "20": "mdi:trash-can",  # Restaffald
    "30": "mdi:food-apple",  # Madaffald
    "40": "mdi:archive",  # Papir & småt pap
    "50": "mdi:bottle-wine",  # Glas & Metal
    "60": "mdi:bottle-soda",  # Plast og mad- & drikkekartoner
}


class Source:
    def __init__(self, address_no: int):
        self.address_no = address_no

    def fetch(self):
        fromDate = datetime.now()
        toDate = datetime.now() + timedelta(days=+365)

        response = requests.get(
            API_URL,
            params={
                "addressNo": self.address_no,
                "startDate": fromDate.isoformat(),
                "endDate": toDate.isoformat(),
                "noCache": False,
            },
        )
        response.raise_for_status()

        months = response.json()["Months"]

        entries = []

        for month in months:
            for day in month["Days"]:
                date = datetime.strptime(day["Date"], "%Y-%m-%dT%H:%M:%S").date()
                for bin in day["Bins"]:
                    entries.append(
                        Collection(
                            date=date,
                            t=bin["Label"],
                            icon=ICON_MAP.get(bin["BinCode"], "mdi:trash-can-outline"),
                        )
                    )

        return entries
