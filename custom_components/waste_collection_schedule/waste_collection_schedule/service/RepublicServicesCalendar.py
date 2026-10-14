"""RepublicServicesCalendar: provider retrieval and parsing using the shared verified HTTP session."""

from datetime import date, datetime, timedelta
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc


class _CalendarClient:
    _session: Any

    def __init__(self, street_address, method=1):
        self._street_address = street_address
        self._method = int(method)

    def retrieve(self):
        s = self._session
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
        r1 = s.get(
            "https://www.republicservices.com/api/v1/publicPickup",
            params={"siteAddressHash": address_hash},
        )
        if r1.status_code == 404:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Republic Services returned no pickup schedule for this address (HTTP 404).",
            )
        r1.raise_for_status()
        r1_data = r1.json().get("data")
        if r1_data is None:
            raise SourceArgumentNotFound(
                "street_address",
                self._street_address,
                "Republic Services does not provide schedule data via their API for this address. This is a known limitation for some service areas (e.g. parts of Massachusetts). Contact Republic Services directly for your collection schedule.",
            )
        services = {
            item["containerCategory"]
            for key, items in r1_data.items()
            if key != "isColaAccount" and isinstance(items, list)
            for item in items
        }
        lobs = sorted({service.lower() for service in services})
        r2 = s.post(
            "https://www.republicservices.com/api/v2/holidaySchedules/schedule",
            json={"latitude": latitude, "longitude": longitude, "lobs": lobs},
        )
        r2.raise_for_status()
        return r1, r2

    def parse(self, raw):
        r1, r2 = raw
        r1_data = r1.json()["data"]
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
        r2_data = r2.json().get("data") or []
        holidays = []
        for item in r2_data:
            if item and item["serviceImpacted"] is True and (item["LOB"] in services):
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
        seen_holidays: set = set()
        deduped_holidays = []
        for holiday in holidays:
            key = (
                holiday["date"],
                holiday["service"],
                holiday["status"],
                holiday["alt_date"],
            )
            if key not in seen_holidays:
                seen_holidays.add(key)
                deduped_holidays.append(holiday)
        holidays = deduped_holidays
        holidays.sort(key=lambda holiday: holiday["date"])

        def affects(holiday, pickup):
            return holiday["service"] == pickup["service"]

        def same_week(day_a, day_b):
            return day_a - timedelta(
                days=(day_a.weekday() + 1) % 7
            ) == day_b - timedelta(days=(day_b.weekday() + 1) % 7)

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
        entries = []
        if self._method == 1:
            for item in schedule:
                entries.append({"date": item["date"], "type": item["waste_type"]})
        elif self._method == 2:
            for item in schedule:
                if (
                    "YARD" in item["waste_description"]
                    or "ORGANICS" in item["waste_description"]
                ):
                    waste_type = "Yard Waste"
                elif "BULK SERVICE" in item["waste_description"]:
                    waste_type = "Bulk Waste"
                elif "RECYCLE" in item["waste_description"]:
                    waste_type = "Recycle"
                else:
                    waste_type = "Solid Waste"
                entries.append({"date": item["date"], "type": waste_type})
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
