from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
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

# Number of months to project the recurring schedule forward
SCHEDULE_MONTHS_AHEAD = 6


def _project_schedule(seed_date: date, period_weeks: int, months_ahead: int) -> list:
    """Generate recurring pickup dates from a seed date.

    Uses the seed date (first known pickup) and projects forward at the given
    interval (period_weeks) for the specified number of months.
    """
    end_date = seed_date + timedelta(days=months_ahead * 30)
    dates = []
    d = seed_date
    while d <= end_date:
        dates.append(d)
        d += timedelta(weeks=period_weeks)
    return dates


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
        r1_json = r1.json().get("data")
        if r1_json is None:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Republic Services does not provide schedule data via their API for this address. This is a known limitation for some service areas (e.g. parts of Massachusetts). Contact Republic Services directly for your collection schedule.",
            )

        # Build schedule by projecting recurring pickup dates forward.
        # The API often returns only the next single date in nextServiceDays for
        # weekly services. We use the weekday frequency fields and period length
        # to project the full recurring schedule, using nextServiceDays[0] as the
        # seed/anchor date.
        service = ""
        schedule = []
        for service_type in r1_json:
            if not hasattr(service_type, "__iter__") or service_type == "isColaAccount":
                continue
            for item in r1_json[service_type]:
                next_days = item.get("nextServiceDays", [])
                if not next_days:
                    continue

                seed_date = datetime.strptime(next_days[0], "%Y-%m-%d").date()
                service = item.get("containerCategory", "")

                # Determine the pickup interval in weeks.
                period_unit = item.get("numberOfPickupsPeriodUnit", "W").strip()
                period_length = int(item.get("numberOfPickupsPeriodLength", 1) or 1)

                # Only project for week-based schedules; for others fall back to
                # using the dates the API already provided.
                if period_unit == "W" and period_length >= 1:
                    pickup_dates = _project_schedule(
                        seed_date, period_length, SCHEDULE_MONTHS_AHEAD
                    )
                else:
                    pickup_dates = [
                        datetime.strptime(d, "%Y-%m-%d").date() for d in next_days
                    ]

                for dt in pickup_dates:
                    schedule.append(
                        {
                            "date": dt,
                            "waste_type": item["wasteTypeDescription"],
                            "waste_description": item["productDescription"],
                            "service": service,
                        }
                    )

        # Compile holidays that impact collections
        r2 = s.get(
            "https://www.republicservices.com/api/v3/holidaySchedules/schedules",
            params={"latitude": latitude, "longitude": longitude},
        )
        r2_json = r2.json()["data"]
        day_offset = 0
        holidays = []
        for item in r2_json:
            if item and item["serviceImpacted"] is True and item["LOB"] == service:
                for delay in DELAYS:
                    if delay in item["description"]:
                        day_offset = DELAYS[delay]
                dt = datetime.strptime(item["date"].split("T")[0], "%Y-%m-%d").date()
                holidays.append(
                    {
                        "date": dt,
                        "name": item["name"],
                        "description": item["description"],
                        "delay": day_offset,
                        "incorporated": False,
                    }
                )

        # Cycle through schedule and holidays incorporating delays.
        # According to Republic Services, "Holidays typically push our residential
        # pickup schedules back one day with regular schedules resuming the
        # following week."
        # Source: https://www.republicservices.com/customer-support/faq
        while True:
            changes = 0
            for holiday in holidays:
                if not holiday["incorporated"]:
                    h = holiday["date"]
                    d = holiday["delay"]
                    for pickup in schedule:
                        p = pickup["date"]
                        # Calculate the next Sunday since Sunday should reset the
                        # scheduled pickup date
                        ns = h + timedelta(days=6 - h.weekday())
                        if h <= p < ns:
                            pickup["date"] = p + timedelta(days=d)
                            holiday["incorporated"] = True
                            changes += 1
            if changes == 0:
                break

        # Build final schedule (implements original logic for assigning icon)
        entries = []
        if self._method == 1:  # Original logic
            for item in schedule:
                if "RECYCLE" in item["waste_description"]:
                    icon = "mdi:recycle"
                elif (
                    "YARD" in item["waste_description"]
                    or "ORGANICS" in item["waste_description"]
                ):
                    icon = "mdi:leaf"
                else:
                    icon = "mdi:trash-can"
                entries.append(
                    Collection(
                        date=item["date"],
                        t=item["waste_type"],
                        icon=icon,
                    ),
                )
        elif self._method == 2:  # Updated to report yard waste as a separate category
            for item in schedule:
                if (
                    "YARD" in item["waste_description"]
                    or "ORGANICS" in item["waste_description"]
                ):
                    icon = "mdi:leaf"
                    waste_type = "Yard Waste"
                elif "BULK SERVICE" in item["waste_description"]:
                    icon = "mdi:leaf"
                    waste_type = "Bulk Waste"
                elif "RECYCLE" in item["waste_description"]:
                    icon = "mdi:recycle"
                    waste_type = "Recycle"
                else:
                    icon = "mdi:trash-can"
                    waste_type = "Solid Waste"

                entries.append(
                    Collection(
                        date=item["date"],
                        t=waste_type,
                        icon=icon,
                    ),
                )

        return entries
