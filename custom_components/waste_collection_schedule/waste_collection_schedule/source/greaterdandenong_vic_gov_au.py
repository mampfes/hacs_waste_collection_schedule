from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Greater Dandenong City Council"
DESCRIPTION = "Source for greaterdandenong.vic.gov.au waste collection."
URL = "https://www.greaterdandenong.vic.gov.au"
TEST_CASES = {
    "45 Ardgower Road Noble Park": {"address": "45 Ardgower Road Noble Park"},
    "8 Foster Street Dandenong": {"address": "8 Foster Street Dandenong"},
}

COUNTRY = "au"

ICON_MAP = {
    "Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
    "Street Sweep": "mdi:broom",
}

BASE_URL = "https://maps.greaterdandenong.com/IntraMaps21B/ApplicationEngine/Integration/api/search/"
API_KEY = "05dbdab3-8568-4d7e-83e0-22cc06a09f7f"
CONFIG_ID = "00000000-0000-0000-0000-000000000000"
SEARCH_FORM = "35f43a60-983b-4c11-ac56-8b1d10e8389f"
DETAILS_FORM = "1ee8052a-e624-45c6-8aee-a2bb990f6a8c"

DAYS = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your address as it appears on the <a href='https://www.greaterdandenong.vic.gov.au/find-my-bin-day'>Find My Bin Day</a> page.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address (e.g. 45 Ardgower Road Noble Park)",
    },
}


class Source:
    def __init__(self, address: str):
        self._address = address

    def fetch(self) -> list[Collection]:
        headers = {"authorization": f"apikey {API_KEY}"}

        # Search for address
        r = requests.get(
            BASE_URL,
            params={
                "ConfigId": CONFIG_ID,
                "form": SEARCH_FORM,
                "fields": self._address,
            },
            headers=headers,
        )
        r.raise_for_status()
        results = r.json()

        if not results:
            raise Exception(f"Address not found: {self._address}")

        # Use first result
        fields = {item["name"]: item["value"] for item in results[0]}
        mapkey = fields["mapkey"]
        dbkey = fields["dbkey"]

        # Get collection details
        r = requests.get(
            BASE_URL,
            params={
                "ConfigId": CONFIG_ID,
                "form": DETAILS_FORM,
                "fields": f"{mapkey},{dbkey}",
            },
            headers=headers,
        )
        r.raise_for_status()
        details = r.json()

        data = {item["name"]: item["value"] for item in details[0]}

        entries = []

        # Waste day is weekly - generate next 4 weeks
        waste_day = data.get("waste_day", "").strip()
        if waste_day in DAYS:
            today = datetime.today().date()
            days_ahead = (DAYS[waste_day] - today.weekday()) % 7
            next_date = today + timedelta(days=days_ahead)
            for i in range(4):
                entries.append(
                    Collection(
                        date=next_date + timedelta(weeks=i),
                        t="Waste",
                        icon=ICON_MAP["Waste"],
                    )
                )

        # Garden day - specific date, fortnightly
        garden_str = data.get("garden_day", "").strip()
        if garden_str:
            try:
                garden_date = datetime.strptime(
                    garden_str.split(", ", 1)[1], "%d %b %Y"
                ).date()
                for i in range(4):
                    entries.append(
                        Collection(
                            date=garden_date + timedelta(weeks=i * 2),
                            t="Garden",
                            icon=ICON_MAP["Garden"],
                        )
                    )
            except (ValueError, IndexError):
                pass

        # Recycling day - specific date, fortnightly
        recycle_str = data.get("recycle_day", "").strip()
        if recycle_str:
            try:
                recycle_date = datetime.strptime(
                    recycle_str.split(", ", 1)[1], "%d %b %Y"
                ).date()
                for i in range(4):
                    entries.append(
                        Collection(
                            date=recycle_date + timedelta(weeks=i * 2),
                            t="Recycling",
                            icon=ICON_MAP["Recycling"],
                        )
                    )
            except (ValueError, IndexError):
                pass

        # Street sweep - specific date
        sweep_str = data.get("street_sweep", "").strip()
        if sweep_str:
            try:
                sweep_date = datetime.strptime(sweep_str, "%d %B %Y").date()
                entries.append(
                    Collection(
                        date=sweep_date,
                        t="Street Sweep",
                        icon=ICON_MAP["Street Sweep"],
                    )
                )
            except ValueError:
                pass

        return entries
