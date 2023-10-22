import json
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Republic Services"
DESCRIPTION = "Source for Republic Services Collection."
URL = "https://www.republicservices.com"
COUNTRY = "us"
TEST_CASES = {
    "Scott Country Clerk": {
        "street_address": "101 E Main St, Georgetown, KY 40324",
        "method": 1,
    },
    "Branch County Clerk": {
        "street_address": "31 Division St. Coldwater, MI 49036",
        "method": "1",
    },
    "Contract Collection": {
        "street_address": "8957 Park Meadows Dr, Elk Grove, CA 95624",
        "method": 2,
    },
    "Residential Collection": {
        "street_address": "117 Roxie Ln, Georgetown, KY 40324",
        "method": "2",
    },
    "No Method arg": {
        "street_address": "8957 Park Meadows Dr, Elk Grove, CA 95624",
    },
}
DELAYS = {
    " one ": 1,
    " two ": 2,
    " three ": 3,
    " four ": 4,
    " five ": 5,
    " six ": 6,
    " seven ": 7,
}


class Source:
    def __init__(self, street_address, method=1):
        self._street_address = street_address
        self._method = int(method)

    def fetch(self):
        s = requests.Session()

        # Get address data
        r0 = requests.get(
            "https://www.republicservices.com/api/v1/addresses",
            params={"addressLine1": self._street_address},
        )
        r0_json = json.loads(r0.text)["data"][0]
        address_hash = r0_json["addressHash"]
        longitude = r0_json["longitude"]
        latitude = r0_json["latitude"]

        # Get raw schedule
        r1 = requests.get(
            "https://www.republicservices.com/api/v1/publicPickup",
            params={"siteAddressHash": address_hash},
        )
        r1_json = json.loads(r1.text)["data"]
        service = ""
        schedule = {}
        for service_type in r1_json:
            if hasattr(service_type, "__iter__") and service_type != "isColaAccount":
                i = 0
                for item in r1_json[service_type]:
                    for day in item["nextServiceDays"]:
                        dt = datetime.strptime(day, "%Y-%m-%d").date()
                        service = item["containerCategory"]
                        schedule.update(
                            {
                                i: {
                                    "date": dt,
                                    "waste_type": item["wasteTypeDescription"],
                                    "waste_description": item["productDescription"],
                                    "service": service,
                                }
                            }
                        )
                        i += 1

        # Compile holidays that impact collections
        r2 = s.get(
            "https://www.republicservices.com/api/v3/holidaySchedules/schedules",
            params={"latitude": latitude, "longitude": longitude},
        )
        r2_json = json.loads(r2.text)["data"]
        day_offset = 0
        i = 0
        holidays = {}
        for item in r2_json:
            if item["serviceImpacted"] is True and item["LOB"] == service:
                for delay in DELAYS:
                    if delay in item["description"]:
                        day_offset = DELAYS[delay]
                dt = datetime.strptime(
                    item["date"], "%Y-%m-%dT00:00:00.0000000Z"
                ).date()
                holidays.update(
                    {
                        i: {
                            "date": dt,
                            "name": item["name"],
                            "description": item["description"],
                            "delay": day_offset,
                            "incorporated": False,
                        }
                    }
                )
                i += 1

        # Cycle through schedule and holidays incorporating delays
        while True:
            changes = 0
            for holiday in holidays:
                if not holidays[holiday]["incorporated"]:
                    h = holidays[holiday]["date"]
                    d = holidays[holiday]["delay"]
                    for pickup in schedule:
                        p = schedule[pickup]["date"]
                        date_difference = (p - h).days
                        if date_difference <= 5 and date_difference >= 0:
                            revised_date = p + timedelta(days=d)
                            schedule[pickup]["date"] = revised_date
                            holidays[holiday]["incorporated"] = True
                            # print(p, h, d, date_difference, revised_date)
                            changes += 1
            if changes == 0:
                break

        # Build final schedule (implements original logic for assigning icon)
        entries = []
        if self._method == 1:  # Original logic
            for item in schedule:
                if "RECYCLE" in schedule[item]["waste_description"]:
                    icon = "mdi:recycle"
                elif "YARD" in schedule[item]["waste_description"]:
                    icon = "mdi:leaf"
                else:
                    icon = "mdi:trash-can"
                entries.append(
                    Collection(
                        date=schedule[item]["date"],
                        t=schedule[item]["waste_type"],
                        icon=icon,
                    ),
                )
        elif (
            self._method == 2
        ):  # Updated to report yard waste as a separate category to recycling
            for item in schedule:
                if "YARD" in schedule[item]["waste_description"]:
                    icon = "mdi:leaf"
                    schedule[item]["waste_type"] = "Yard Waste"
                elif "RECYCLE" in schedule[item]["waste_description"]:
                    icon = "mdi:recycle"
                elif "YARD" in schedule[item]["waste_description"]:
                    icon = "mdi:leaf"
                else:
                    icon = "mdi:trash-can"
                entries.append(
                    Collection(
                        date=schedule[item]["date"],
                        t=schedule[item]["waste_type"],
                        icon=icon,
                    ),
                )

        return entries
