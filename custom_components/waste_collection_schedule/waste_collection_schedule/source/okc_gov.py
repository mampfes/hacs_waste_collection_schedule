import re
from datetime import date, datetime, timedelta
from urllib.parse import quote

import requests
from waste_collection_schedule import Collection, Icons

TITLE = "City of Oklahoma City"
DESCRIPTION = "Source for OKC Open Data Portal and okc.schizo.dev services for City of Oklahoma City"
URL = "https://www.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Test_001": {"objectID": "1781151"},
    "Test_002": {"objectID": "2002902"},
    "Test_003": {"objectID": 1935340},
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en,en-GB;q=0.7,en-US;q=0.3",
    "Upgrade-Insecure-Requests": "1",
}
# OKC Open Data Portal ArcGIS endpoints (accessible)
TRASH_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1"
RECYCLE_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3"
BULKY_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2"

UNOFFICIAL_URL = "https://okc.schizo.dev/trash"

# Waste layer mapping for official API
WASTE_LAYERS = {
    "TRASH": TRASH_ZONES_URL,
    "RECYCLE": RECYCLE_ZONES_URL,
    "BULKY": BULKY_ZONES_URL,
}
WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
ICON_MAP = {
    "TRASH": Icons.GENERAL_WASTE,
    "RECYCLE": Icons.RECYCLING,
    "BULKY": Icons.BULKY,
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "objectID": "Object ID for unofficial source (okc.schizo.dev).",
        "try_official": "Enable official OKC Open Data Portal services (requires Object IDs).",
        "bulkyObjectID": "Object ID for bulky waste zone from OKC Open Data Portal.",
        "recycleObjectID": "Object ID for recycling zone from OKC Open Data Portal.",
        "trashObjectID": "Object ID for trash collection zone from OKC Open Data Portal.",
        "recycle_reference_date": "Known recycling pickup date (e.g., '2025-06-05'). Use to fix every other week schedule when dates are incorrect.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "For official mode with try_official=true, provide specific Object IDs from OKC Open Data Portal "
    "(bulkyObjectID, recycleObjectID, trashObjectID). "
    "Object IDs can be found by exploring the OKC waste collection datasets at "
    "https://utility.arcgis.com/usrsvcs/servers. "
    "If try_official is disabled, provide objectID for the unofficial source."
}


class Source:
    def __init__(
        self,
        objectID: str = "",
        try_official: bool = False,
        bulkyObjectID: str = "",
        recycleObjectID: str = "",
        trashObjectID: str = "",
        recycle_reference_date: str = "",
    ):
        if isinstance(try_official, bool):
            self._try_official = try_official
        else:
            self._try_official = str(try_official).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
        self._object_id = str(objectID).strip()
        self._recycle_reference_date = str(recycle_reference_date).strip()
        self._record_ids = {
            "BULKY": str(bulkyObjectID).strip(),
            "RECYCLE": str(recycleObjectID).strip(),
            "TRASH": str(trashObjectID).strip(),
        }

        if self._try_official:
            missing = [
                waste_type
                for waste_type, record_id in self._record_ids.items()
                if record_id == ""
            ]
            if missing:
                raise Exception(
                    "Missing official Object IDs for: "
                    + ", ".join(missing)
                    + ". Provide bulkyObjectID, recycleObjectID, trashObjectID."
                )
        elif self._object_id == "":
            raise Exception(
                "objectID is required when try_official is disabled (unofficial source mode)."
            )

    def _query_object_id(self, layer_url: str, object_id: str) -> dict:
        """Query a waste layer for a specific Object ID using ArcGIS FeatureServer."""
        params = {
            "where": f"OBJECTID={object_id}",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
        }
        
        try:
            response = requests.get(
                f"{layer_url}/query",
                params=params,
                headers=HEADERS,
                timeout=10,
            )
            response.raise_for_status()
            
            json_data = response.json()
            features = json_data.get("features", [])
            if features:
                return features[0].get("attributes", {})
            else:
                raise Exception(f"No record found with OBJECTID={object_id}")
                        
        except Exception as e:
            raise Exception(f"Unable to query Object ID {object_id}: {str(e)}")
    
    def _parse_arcgis_pickup_dates(self, attributes: dict, waste_type: str) -> list:
        """Parse pickup dates from ArcGIS attributes."""
        today = datetime.now().date()
        entries = []
        
        # Check for specific pickup dates (NextPick1, NextPick2, NextPick3)
        for i in range(1, 4):
            pickup_date_key = f"NextPick{i}"
            if pickup_date_key in attributes and attributes[pickup_date_key]:
                try:
                    timestamp_ms = attributes[pickup_date_key]
                    if isinstance(timestamp_ms, (int, float)):
                        pickup_date = datetime.fromtimestamp(timestamp_ms / 1000).date()
                        if pickup_date >= today:
                            entries.append(
                                Collection(
                                    date=pickup_date,
                                    t=waste_type,
                                    icon=ICON_MAP.get(waste_type),
                                )
                            )
                except Exception:
                    pass
        
        if not entries:
            # Handle PickupDay field variations
            pickup_day = None
            for field_name in ["PickupDay", "PickUpDay", "PICKUPDAY"]:
                if field_name in attributes and attributes[field_name]:
                    pickup_day = str(attributes[field_name]).strip()
                    break
            
            if pickup_day:
                try:
                    next_date = self._resolve_pickup_date(pickup_day, today, waste_type)
                    entries.append(
                        Collection(
                            date=next_date,
                            t=waste_type,
                            icon=ICON_MAP.get(waste_type),
                        )
                    )
                except Exception:
                    pass
        
        return entries

    def _next_weekday(self, weekday_name: str, today: date) -> date:
        target_weekday = WEEKDAY_INDEX[weekday_name.lower()]
        days_ahead = (target_weekday - today.weekday()) % 7
        return today + timedelta(days=days_ahead)

    def _nth_weekday_of_month(
        self, year: int, month: int, weekday_index: int, nth: int
    ) -> date | None:
        first_day = date(year, month, 1)
        delta_to_weekday = (weekday_index - first_day.weekday()) % 7
        candidate = first_day + timedelta(days=delta_to_weekday + (nth - 1) * 7)
        if candidate.month != month:
            return None
        return candidate

    def _next_nth_weekday(self, nth: int, weekday_name: str, today: date) -> date:
        weekday_index = WEEKDAY_INDEX[weekday_name.lower()]
        year = today.year
        month = today.month

        for _ in range(24):
            candidate = self._nth_weekday_of_month(year, month, weekday_index, nth)
            if candidate is not None and candidate >= today:
                return candidate

            month += 1
            if month > 12:
                month = 1
                year += 1

        raise Exception(
            f"Unable to calculate next '{nth}' '{weekday_name}' date from {today}."
        )

    def _resolve_pickup_date(self, pickup_rule: str, today: date, waste_type: str = "") -> date:
        normalized_rule = pickup_rule.strip()
        normalized_rule_lower = normalized_rule.lower()

        # If this is RECYCLE and we have a reference date, use it for every-other-week calculation
        if waste_type.upper() == "RECYCLE" and self._recycle_reference_date:
            try:
                # Parse reference date (try different formats)
                ref_date = None
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                    try:
                        ref_date = datetime.strptime(self._recycle_reference_date, fmt).date()
                        break
                    except ValueError:
                        continue
                
                # Check if the pickup_rule is a weekday (like "friday") and we parsed a valid ref_date
                if ref_date and normalized_rule_lower in WEEKDAY_INDEX:
                    # Use reference date as starting point for pattern
                    if ref_date >= today:
                        return ref_date
                    
                    # Calculate weeks difference
                    weeks_diff = (today - ref_date).days // 7
                    
                    # Determine next date based on parity
                    if weeks_diff % 2 == 0:
                        next_date = ref_date + timedelta(weeks=2)
                    else:
                        next_date = ref_date + timedelta(weeks=1)
                    
                    # Make sure date is after today
                    while next_date <= today:
                        next_date += timedelta(weeks=2)
                    
                    return next_date
            except Exception:
                # Fall through to normal logic on any error
                pass

        if normalized_rule_lower in WEEKDAY_INDEX:
            return self._next_weekday(normalized_rule_lower, today)

        ordinal_match = re.match(
            r"^(?P<nth>[1-5])(st|nd|rd|th)\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)$",
            normalized_rule_lower,
        )
        if ordinal_match:
            nth = int(ordinal_match.group("nth"))
            weekday = ordinal_match.group("weekday")
            return self._next_nth_weekday(nth, weekday, today)

        for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(normalized_rule, date_format).date()
            except ValueError:
                continue

        raise Exception(f"Unsupported pickup rule returned by API: '{pickup_rule}'")

    def _fetch_unofficial(self):
        response = requests.get(
            UNOFFICIAL_URL,
            params={"recordID": self._object_id},
            headers=HEADERS,
        )
        response.raise_for_status()

        try:
            json_data = response.json()
        except Exception as e:
            raise Exception(
                f"Invalid response returned from source: {UNOFFICIAL_URL}"
            ) from e

        # Current unofficial endpoint returns nested objects with explicit pickup dates.
        if isinstance(json_data, dict) and any(
            key in json_data for key in ("trash", "recycling", "bulkyWaste")
        ):
            today = datetime.now().date()
            entries = []

            def _first_upcoming_pickup_date(pickups):
                for pickup in pickups or []:
                    pickup_date = (
                        pickup.get("date") if isinstance(pickup, dict) else None
                    )
                    if not pickup_date:
                        continue
                    try:
                        parsed_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
                    except ValueError:
                        continue
                    if parsed_date >= today:
                        return parsed_date

                return None

            trash_data = json_data.get("trash", {})
            trash_date = None
            if isinstance(trash_data, dict):
                next_date = trash_data.get("next", {}).get("date")
                if next_date:
                    try:
                        trash_date = datetime.strptime(next_date, "%Y-%m-%d").date()
                        if trash_date < today:
                            trash_date = None
                    except ValueError:
                        trash_date = None
                if trash_date is None and trash_data.get("day"):
                    trash_date = self._resolve_pickup_date(
                        str(trash_data["day"]), today, "TRASH"
                    )

            if trash_date is not None:
                entries.append(
                    Collection(date=trash_date, t="TRASH", icon=ICON_MAP.get("TRASH"))
                )

            recycling_data = json_data.get("recycling", {})
            recycle_date = None
            if isinstance(recycling_data, dict):
                recycle_date = _first_upcoming_pickup_date(
                    recycling_data.get("pickups")
                )
                if recycle_date is None and recycling_data.get("day"):
                    recycle_date = self._resolve_pickup_date(
                        str(recycling_data["day"]), today, "RECYCLE"
                    )

            if recycle_date is not None:
                entries.append(
                    Collection(
                        date=recycle_date,
                        t="RECYCLE",
                        icon=ICON_MAP.get("RECYCLE"),
                    )
                )

            bulky_data = json_data.get("bulkyWaste", {})
            bulky_date = None
            if isinstance(bulky_data, dict):
                bulky_date = _first_upcoming_pickup_date(bulky_data.get("pickups"))
                if bulky_date is None and bulky_data.get("schedule"):
                    bulky_date = self._resolve_pickup_date(
                        str(bulky_data["schedule"]), today, "BULKY"
                    )

            if bulky_date is not None:
                entries.append(
                    Collection(date=bulky_date, t="BULKY", icon=ICON_MAP.get("BULKY"))
                )

            if entries:
                return entries

        records = json_data.get("Records")
        if records is None:
            records = json_data.get("records")
        if not records:
            raise Exception(
                "No records found for objectID in unofficial source. Please verify your objectID."
            )

        fields = json_data.get("Fields")
        if fields is None:
            fields = json_data.get("fields", [])

        record = records[0]
        if len(record) != len(fields):
            raise Exception("Invalid record format returned from unofficial source")

        today = datetime.now().date()
        entries = []

        for field, raw_value in zip(fields, record):
            field_name = str(field.get("FieldName", ""))

            if field_name in {"Notice", "Shape"} or not field_name.startswith("Next_"):
                continue

            if raw_value is None:
                continue

            value = str(raw_value).strip()
            if value == "" or value.lower() == "not available":
                continue

            waste_type = field_name.replace("Next_", "").split("_")[0].upper()
            entries.append(
                Collection(
                    date=self._resolve_pickup_date(value, today, waste_type),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries

    def _fetch_official(self):
        today = datetime.now().date()
        entries = []

        for waste_type, object_id in self._record_ids.items():
            if not object_id:
                continue
            try:
                layer_url = WASTE_LAYERS[waste_type]
                attributes = self._query_object_id(layer_url, object_id)
                layer_entries = self._parse_arcgis_pickup_dates(attributes, waste_type)
                if layer_entries:
                    entries.extend(layer_entries)
            except Exception:
                continue
        
        if entries:
            return entries
        
        raise Exception(
            "No waste collection data found for the provided Object IDs. "
            "Verify the Object IDs are correct and correspond to the appropriate waste types."
        )

    def fetch(self):
        if self._try_official:
            return self._fetch_official()

        return self._fetch_unofficial()
