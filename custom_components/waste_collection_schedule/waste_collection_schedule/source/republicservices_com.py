from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

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
    "4420 Oasis Hill Ave, North Las Vegas, NV 89085": {
        "street_address": "4420 Oasis Hill Ave, North Las Vegas, NV 89085",
        "method": 2,
    },
    # Friday pickup in a division whose Thanksgiving/Christmas are a one-day delay,
    # so the holiday adjustment moves the Friday collection to Saturday.
    "Friday holiday delay": {
        "street_address": "104 Fizer Dr, Georgetown, KY 40324",
        "method": 2,
    },
    # Division where Independence Day is "Not Running" rather than a delay, exercising
    # the cancellation branch.
    "Not Running holiday": {
        "street_address": "700 E Warm Springs Ave, Boise, ID 83712",
        "method": 2,
    },
}


class Source:
    def __init__(self, street_address, method=1):
        self._street_address = street_address
        self._method = int(method)

    def fetch(self):
        s = requests.Session()

        # Get address data
        r0 = s.get(
            "https://www.republicservices.com/api/v1/addresses",
            params={"addressLine1": self._street_address},
        )
        r0.raise_for_status()
        r0_data = r0.json().get("data")
        if not r0_data:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "No address found matching the provided street address.",
            )
        r0_json = r0_data[0]
        address_hash = r0_json["addressHash"]
        longitude = r0_json["longitude"]
        latitude = r0_json["latitude"]

        # Get raw schedule
        r1 = s.get(
            "https://www.republicservices.com/api/v1/publicPickup",
            params={"siteAddressHash": address_hash},
        )
        r1.raise_for_status()
        r1_data = r1.json().get("data")
        if r1_data is None:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Republic Services does not provide schedule data via their API for this address. "
                "This is a known limitation for some service areas (e.g. parts of Massachusetts). "
                "Contact Republic Services directly for your collection schedule.",
            )

        services: set = set()
        schedule = []
        today = date.today()
        end_date = today + timedelta(days=182)

        for service_type in r1_data:
            if hasattr(service_type, "__iter__") and service_type != "isColaAccount":
                for item in r1_data[service_type]:
                    period_length = item.get("numberOfPickupsPeriodLength", 1)
                    period_unit = item.get("numberOfPickupsPeriodUnit", "")
                    service = item["containerCategory"]
                    services.add(service)

                    if (
                        period_unit
                        and period_unit.lower() in ("w", "week")
                        and item.get("nextServiceDays")
                    ):
                        # Project recurring weekly/fortnightly schedule from seed date
                        seed = datetime.strptime(
                            item["nextServiceDays"][0], "%Y-%m-%d"
                        ).date()
                        interval = timedelta(weeks=period_length)
                        current = seed
                        while current <= end_date:
                            schedule.append(
                                {
                                    "date": current,
                                    "waste_type": item["wasteTypeDescription"],
                                    "waste_description": item["productDescription"],
                                    "service": service,
                                }
                            )
                            current += interval
                    else:
                        for day in item["nextServiceDays"]:
                            dt = datetime.strptime(day, "%Y-%m-%d").date()
                            schedule.append(
                                {
                                    "date": dt,
                                    "waste_type": item["wasteTypeDescription"],
                                    "waste_description": item["productDescription"],
                                    "service": service,
                                }
                            )

        # Compile holidays that impact collections.
        # The v3 GET endpoint the old code used returns an empty payload ({"data":[null]})
        # for every address tested, so no adjustment was ever applied. The site itself
        # uses a v2 POST that takes the lines of business as a body. Request the LOBs
        # we actually have containers for so commercial/industrial keep working too.
        lobs = sorted({service.lower() for service in services})
        r2 = s.post(
            "https://www.republicservices.com/api/v2/holidaySchedules/schedule",
            json={"latitude": latitude, "longitude": longitude, "lobs": lobs},
        )
        r2.raise_for_status()
        r2_data = r2.json().get("data") or []
        holidays = []
        for item in r2_data:
            if item and item["serviceImpacted"] is True and item["LOB"] in services:
                dt = datetime.strptime(item["date"].split("T")[0], "%Y-%m-%d").date()
                holidays.append(
                    {
                        "date": dt,
                        "name": item["name"],
                        "service": item["LOB"],
                        "status": (item.get("holidaySchedule") or "").lower(),
                        "alt_date": item.get("altPickUpDate"),
                    }
                )
        # The site applies holidays oldest-first, so a run of holidays in one week can
        # push a pickup forward day by day. Match that ordering.
        holidays.sort(key=lambda holiday: holiday["date"])

        # A holiday only affects the line of business it belongs to, so match each holiday
        # to pickups of the same service. The API returns one holiday per line of business,
        # so ignoring this would shift a pickup once per business line it happens to have.
        def affects(holiday, pickup):
            return holiday["service"] == pickup["service"]

        # Reproduce the three behaviours the website applies to an impacted pickup:
        #   "Not Running"    -> the collection is cancelled with no make-up day
        #   "Service Moved"  -> the collection jumps to the alternate date the API supplies
        #   "One Day Delay"  -> the collection and every later same-week collection slide
        #                       forward one day (a Sunday-start week, on-or-after the holiday)
        def same_week(day_a, day_b):
            # Sunday-start week, matching the site's areDatesInSameWeek
            return day_a - timedelta(days=(day_a.weekday() + 1) % 7) == day_b - timedelta(
                days=(day_b.weekday() + 1) % 7
            )

        not_running = {
            (h["date"], h["service"]) for h in holidays if h["status"] == "not running"
        }
        schedule = [
            pickup
            for pickup in schedule
            if (pickup["date"], pickup["service"]) not in not_running
        ]

        for holiday in holidays:
            h = holiday["date"]
            if holiday["status"] == "service moved" and holiday["alt_date"]:
                alt = datetime.strptime(
                    holiday["alt_date"].split("T")[0], "%Y-%m-%d"
                ).date()
                for pickup in schedule:
                    if affects(holiday, pickup) and pickup["date"] == h:
                        pickup["date"] = alt
            elif holiday["status"] == "one day delay":
                for pickup in schedule:
                    if (
                        affects(holiday, pickup)
                        and pickup["date"] >= h
                        and same_week(h, pickup["date"])
                    ):
                        pickup["date"] = pickup["date"] + timedelta(days=1)

        # Build final schedule
        entries = []
        if self._method == 1:
            for item in schedule:
                if "RECYCLE" in item["waste_description"]:
                    icon = Icons.RECYCLING
                elif (
                    "YARD" in item["waste_description"]
                    or "ORGANICS" in item["waste_description"]
                ):
                    icon = Icons.ORGANIC
                else:
                    icon = Icons.GENERAL_WASTE
                entries.append(
                    Collection(
                        date=item["date"],
                        t=item["waste_type"],
                        icon=icon,
                    ),
                )
        elif self._method == 2:
            for item in schedule:
                if (
                    "YARD" in item["waste_description"]
                    or "ORGANICS" in item["waste_description"]
                ):
                    icon = Icons.ORGANIC
                    waste_type = "Yard Waste"
                elif "BULK SERVICE" in item["waste_description"]:
                    icon = Icons.BULKY
                    waste_type = "Bulk Waste"
                elif "RECYCLE" in item["waste_description"]:
                    icon = Icons.RECYCLING
                    waste_type = "Recycle"
                else:
                    icon = Icons.GENERAL_WASTE
                    waste_type = "Solid Waste"

                entries.append(
                    Collection(
                        date=item["date"],
                        t=waste_type,
                        icon=icon,
                    ),
                )

        return entries
