from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Denbighshire County Council"
DESCRIPTION = "Source for Denbighshire County Council."
URL = "https://www.denbighshire.gov.uk/"
TEST_CASES = {
    "10003928409": {"uprn": "10003928409"},
    "100100183412": {"uprn": 100100183412},
    "10003928445": {"uprn": "10003928445"},
}

ICON_MAP = {
    "garden": "mdi:leaf",
    "food": "mdi:food",
    "refuse": "mdi:trash-can",
    "recycling": "mdi:recycle",
}

API_URL = "https://refusecalendarapi.denbighshire.gov.uk/Calendar/{uprn}"
X_CSRF_TOKEN_URL = "https://refusecalendarapi.denbighshire.gov.uk/Csrf/token"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str | int = uprn

    def fetch(self):
        r = requests.get(X_CSRF_TOKEN_URL)
        r.raise_for_status()

        r = requests.get(
            API_URL.format(uprn=self._uprn), headers={"X-CSRF-TOKEN": r.json()["token"]}
        )
        r.raise_for_status()

        entries = []

        for key, value in r.json().items():
            if not key.endswith("Date") or not value:
                continue
            bin_types = [key.replace("Date", "").lower()]
            if bin_types[0] == "recycling":
                bin_types.append("food")
            date = datetime.strptime(value, "%d/%m/%Y").date()

            for bin_type in bin_types:
                entries.append(
                    Collection(date=date, t=bin_type, icon=ICON_MAP.get(bin_type))
                )

        return entries
