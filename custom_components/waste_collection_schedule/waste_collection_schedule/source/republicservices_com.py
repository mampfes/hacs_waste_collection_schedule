import requests
import json

from datetime import datetime, timedelta
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Republic Services"
DESCRIPTION = "Source for Republic Services Collection."
URL = "https://www.republicservices.com"
COUNTRY = "us"
TEST_CASES = {
    "Scott Country Clerk": {"street_address": "101 E Main St, Georgetown, KY 40324"},
    "Branch County Clerk": {"street_address": "31 Division St. Coldwater, MI 49036"},
    "Contract Collection": {"street_address": "8957 Park Meadows Dr, Elk Grove, CA 95624"},

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
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        s = requests.Session()

        # get address data
        r0 = requests.get(
            "https://www.republicservices.com/api/v1/addresses",
            params={"addressLine1": self._street_address},
        )
        r0_json = json.loads(r0.text)["data"][0]

        address_hash = r0_json["addressHash"]
        longitude = r0_json["longitude"]
        latitude = r0_json["latitude"]
        # postal = r0_json["postalCode"]
        service = ""
        day_offset = 0

        # get raw schedule and build dict
        r1 = requests.get(
            "https://www.republicservices.com/api/v1/publicPickup",
            params={"siteAddressHash": address_hash},
        )
        r1_json = json.loads(r1.text)["data"]

        schedule = {}
        for service_type in r1_json:
            if hasattr(service_type, "__iter__") and service_type != "isColaAccount":
                i = 0
                for item in r1_json[service_type]:
                    for day in item["nextServiceDays"]:
                        dt = datetime.strptime(day, "%Y-%m-%d").date()
                        service = item["containerCategory"]
                        schedule.update(
                            {i: {
                                "date": dt,
                                "waste_type": item["wasteTypeDescription"],
                                "waste_description": item["productDescription"],
                                "service": service,
                                }
                            }
                        )
                        i += 1

        # compile holidays that impact collections
        r3 = s.get(f"https://www.republicservices.com/api/v3/holidaySchedules/schedules", params={"latitude": latitude, "longitude": longitude})
        r3_json = json.loads(r3.text)["data"]

        i = 0
        holidays = {}
        for item in r3_json:
            if item["serviceImpacted"] == True and item["LOB"] == service:
                for delay in DELAYS:
                    if delay in item["description"]:
                        day_offset = DELAYS[delay]
                dt = datetime.strptime(item["date"], "%Y-%m-%dT00:00:00.0000000Z").date()
                holidays.update(
                    {i: {
                        "date": dt,
                        "name": item["name"],
                        "description": item["description"],
                        "delay": day_offset,
                        }
                    }
                )
                i += 1

        # keep adjusting dates until they're not impacted by holidays
        while True:
            changes = 0
            for pickup in schedule:
                p = schedule[pickup]["date"]
                for holiday in holidays:
                    h = holidays[holiday]["date"]
                    d = holidays[holiday]["delay"]
                    date_difference = (h - p).days
                    if date_difference <= 5 and date_difference >=0: # is this right???
                        revised_date = p + timedelta(days = d)
                        schedule[pickup]["date"] = revised_date
                        # increment marker
                        changes += 1
            if changes == 0:
                break

        # build final schedule (implements original logic for assigning icon)
        entries = []
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
        
        return entries
