from datetime import datetime

import requests
from dateutil.parser import parse as dateparse
from dateutil.rrule import WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

TITLE = "City of Melville"
DESCRIPTION = "Source for City of Melville waste collection."
URL = "https://www.melvillecity.com.au"
COUNTRY = "au"

TEST_CASES = {
    "Williams Road": {"address": "43 Williams Road, Melville, WA"},
    "Canning Highway": {"address": "356 Canning Highway, Bicton, WA"},
}

ICON_MAP = {
    "FOGO": "mdi:leaf",
    "General Waste": "mdi:trash-can",
    "Recycling": "mdi:recycle",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street address including suburb "
    "(e.g. '43 Williams Road, Melville, WA'). "
    "Search at https://www.melvillecity.com.au/waste-and-environment/waste-recycling-fogo/residential-bins",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with suburb (e.g. '43 Williams Road, Melville, WA')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

INTRAMAPS_BASE = "https://melville.spatial.t1cloud.com/spatial/intramaps/applicationengine/Integration/api"
CONFIG_ID = "3f105b05-d2ee-419c-8265-1ab592559a33"
PROJECT_ID = "78ad3422-3dd6-4540-b318-782d4d1313a0"
WASTE_FORM_ID = "0e72c05c-0181-428a-b4e0-e2be69cf69dc"
API_KEY = "bb6fcd4c-7de3-4ce5-8f6d-dc3335ffb26e"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

WEEKDAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


class Source:
    def __init__(self, address: str):
        if not address:
            raise SourceArgumentRequired("address", "A street address is required")
        self._address = address.strip()

    def fetch(self) -> list[Collection]:
        headers = {
            "Authorization": f"apikey {API_KEY}",
            "Content-Type": "application/json",
        }

        # Step 1: Geocode address via Nominatim
        r = requests.get(
            NOMINATIM_URL,
            params={
                "q": self._address,
                "format": "json",
                "limit": "1",
                "countrycodes": "au",
            },
            headers={"User-Agent": "hacs_waste_collection_schedule"},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise SourceArgumentNotFound("address", self._address)

        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])

        # Step 2: Reproject from EPSG:4326 to EPSG:7850
        r = requests.get(
            f"{INTRAMAPS_BASE}/Reproject",
            params={
                "configId": CONFIG_ID,
                "project": PROJECT_ID,
                "x": str(lng),
                "y": str(lat),
                "epsg": "epsg:4326",
                "epsgout": "epsg:7850",
            },
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        proj = r.json()

        # Step 3: Query waste collection zone
        r = requests.get(
            f"{INTRAMAPS_BASE}/search/",
            params={
                "configId": CONFIG_ID,
                "project": PROJECT_ID,
                "form": WASTE_FORM_ID,
                "fields": f"{proj['x']},{proj['y']}",
            },
            headers=headers,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        if not data or not data[0]:
            raise SourceArgumentNotFound("address", self._address)

        # Parse response fields
        fields = {item["name"]: item["value"] for item in data[0]}

        entries = []

        # GreenLid (FOGO) — weekly
        if "GreenLid" in fields:
            day_name = fields.get("collection_district", "")
            weekday = WEEKDAYS.get(day_name)
            if weekday is not None:
                for d in rrule(
                    WEEKLY,
                    byweekday=weekday,
                    dtstart=datetime.now(),
                    count=26,
                ):
                    entries.append(
                        Collection(date=d.date(), t="FOGO", icon=ICON_MAP["FOGO"])
                    )

        # RedLid (General Waste) — fortnightly, next date given
        if "RedLid" in fields and fields["RedLid"]:
            try:
                next_red = dateparse(fields["RedLid"], dayfirst=True).date()
                for d in rrule(WEEKLY, interval=2, dtstart=next_red, count=13):
                    entries.append(
                        Collection(
                            date=d.date(),
                            t="General Waste",
                            icon=ICON_MAP["General Waste"],
                        )
                    )
            except (ValueError, TypeError):
                pass

        # YellowLid (Recycling) — fortnightly, next date given
        if "YellowLid" in fields and fields["YellowLid"]:
            try:
                next_yellow = dateparse(fields["YellowLid"], dayfirst=True).date()
                for d in rrule(WEEKLY, interval=2, dtstart=next_yellow, count=13):
                    entries.append(
                        Collection(
                            date=d.date(),
                            t="Recycling",
                            icon=ICON_MAP["Recycling"],
                        )
                    )
            except (ValueError, TypeError):
                pass

        return entries
