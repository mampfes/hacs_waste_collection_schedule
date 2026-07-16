import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Oklahoma City"
DESCRIPTION = "Source for the City of Oklahoma City waste collection schedule. Supports the unofficial okc.schizo.dev API (single recordID) and the official OKC Open Data Portal (ArcGIS) waste collection zones."
URL = "https://www.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Unofficial (schizo.dev) recordID": {
        "recordID": "1781503",
    },
    "Trash Fri / Recycle Mon / Bulky 4th Mon": {
        "trashObjectID": 1,
        "recycleObjectID": 1215,
        "bulkyObjectID": 1,
    },
    "Recycle every other week (anchored)": {
        "recycleObjectID": 1215,
        "recycle_reference_date": "2026-06-15",
    },
    "Recycle Fri every other week (anchored, live zone)": {
        "recycleObjectID": 1366,
        "recycle_reference_date": "2026-06-19",
    },
    "Trash only": {
        "trashObjectID": 2,
    },
}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en,en-GB;q=0.7,en-US;q=0.3",
    "Upgrade-Insecure-Requests": "1",
}

# Unofficial community API (single recordID covers trash, recycling and bulky).
UNOFFICIAL_URL = "https://okc.schizo.dev/trash"

# OKC Open Data Portal ArcGIS FeatureServer endpoints
TRASH_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/45426e5e1b31489db9afea603870f724/rest/services/OpenData/Utilities/FeatureServer/1"
RECYCLE_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/0f286e1243ca4bb39a70e323b1608222/rest/services/OpenData/Utilities/FeatureServer/3"
BULKY_ZONES_URL = "https://utility.arcgis.com/usrsvcs/servers/c4455716f4bf4d1dafe6806e0e619de8/rest/services/OpenData/Utilities/FeatureServer/2"

# Waste type -> (FeatureServer layer URL, constructor argument name)
WASTE_LAYERS = {
    "TRASH": (TRASH_ZONES_URL, "trashObjectID"),
    "RECYCLE": (RECYCLE_ZONES_URL, "recycleObjectID"),
    "BULKY": (BULKY_ZONES_URL, "bulkyObjectID"),
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

PARAM_DESCRIPTIONS = {
    "en": {
        "recordID": "Record ID for the unofficial okc.schizo.dev source. This single ID covers trash, recycling and bulky waste. Go to https://okc.schizo.dev and type in your address to get it. This is the easiest option and is recommended.",
        "trashObjectID": "OBJECTID of your trash collection zone. Go to https://open-okc.hub.arcgis.com/datasets/45426e5e1b31489db9afea603870f724_1/explore?location=35.566301%2C-97.260765%2C10 , zoom into your house and click your zone — the OBJECTID is shown in the info popup. Used on its own, or as a fallback if the unofficial recordID source is unavailable.",
        "recycleObjectID": "OBJECTID of your recycling zone. Go to https://open-okc.hub.arcgis.com/datasets/0f286e1243ca4bb39a70e323b1608222_3/explore?location=35.486250%2C-97.582400%2C11 , zoom into your house and click your zone — the OBJECTID is shown in the info popup. Used on its own, or as a fallback if the unofficial recordID source is unavailable.",
        "bulkyObjectID": "OBJECTID of your bulky waste zone. Go to https://data.okc.gov/portal/page/viewer?datasetName=Bulky%20Waste%20Zones&view=map , find your house on the map, then switch to the Table view and filter by map to read your OBJECTID. Used on its own, or as a fallback if the unofficial recordID source is unavailable.",
        "recycle_reference_date": "Optional ISO date (YYYY-MM-DD) of a known recycling collection. OKC recycling runs every other week, but the official data portal only exposes a weekday; provide one real pickup date so the alternating-week schedule can be calculated correctly. Not needed when using recordID.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Recommended: go to https://okc.schizo.dev , type in your address, and copy the record ID it "
    "shows into recordID. That single ID covers trash, recycling and bulky waste. If your address "
    "isn't found, try variations (e.g. drop a leading 'N'/'North' so '1234 N Sample St' becomes "
    "'1234 Sample St'). "
    "Alternatively, use the official OKC data portals to find one OBJECTID per waste type: "
    "for trash, open https://open-okc.hub.arcgis.com/datasets/45426e5e1b31489db9afea603870f724_1/explore?location=35.566301%2C-97.260765%2C10 , "
    "zoom into your house, click your zone and read the OBJECTID from the info popup. "
    "For recycling, do the same at https://open-okc.hub.arcgis.com/datasets/0f286e1243ca4bb39a70e323b1608222_3/explore?location=35.486250%2C-97.582400%2C11 . "
    "For bulky waste, open https://data.okc.gov/portal/page/viewer?datasetName=Bulky%20Waste%20Zones&view=map , "
    "find your house on the map, then switch to the Table view and filter by map to read your OBJECTID. "
    "With the official method, recycling is collected every other week and the portal only reports "
    "the weekday, so also set recycle_reference_date to one date you know recycling was (or will "
    "be) collected to pin the correct week. If both recordID and official OBJECTIDs are provided, "
    "the unofficial recordID source is used first and falls back to the official OBJECTIDs if it "
    "fails or returns nothing."
}


class Source:
    def __init__(
        self,
        recordID: str | int = "",
        trashObjectID: str | int = "",
        recycleObjectID: str | int = "",
        bulkyObjectID: str | int = "",
        recycle_reference_date: str = "",
    ):
        self._record_id = str(recordID).strip()
        self._object_ids = {
            "TRASH": str(trashObjectID).strip(),
            "RECYCLE": str(recycleObjectID).strip(),
            "BULKY": str(bulkyObjectID).strip(),
        }

        self._recycle_reference_date: date | None = None
        if str(recycle_reference_date).strip():
            try:
                self._recycle_reference_date = datetime.strptime(
                    str(recycle_reference_date).strip(), "%Y-%m-%d"
                ).date()
            except ValueError as exc:
                raise SourceArgumentNotFound(
                    "recycle_reference_date",
                    recycle_reference_date,
                    "must be an ISO date (YYYY-MM-DD) of a known recycling pickup.",
                ) from exc

        if not self._record_id and not any(self._object_ids.values()):
            raise SourceArgumentNotFound(
                "recordID",
                "",
                "provide recordID (unofficial source) or at least one of "
                "trashObjectID, recycleObjectID or bulkyObjectID (official source).",
            )

    def _query_object_id(self, layer_url: str, object_id: str, argument: str) -> dict:
        """Query a waste layer for a specific OBJECTID using the ArcGIS FeatureServer."""
        params = {
            "where": f"OBJECTID={object_id}",
            "outFields": "*",
            "returnGeometry": "false",
            "f": "json",
        }

        response = requests.get(
            f"{layer_url}/query",
            params=params,
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        json_data = response.json()
        features = json_data.get("features", [])
        if not features:
            raise SourceArgumentNotFound(
                argument,
                object_id,
                "no zone found with this OBJECTID in the OKC Open Data Portal.",
            )
        return features[0].get("attributes", {})

    def _parse_pickup_dates(self, attributes: dict, waste_type: str) -> list:
        """Parse the pickup schedule from ArcGIS attributes into Collections."""
        today = datetime.now().date()
        entries: list = []

        # Recycling runs every other week, but the ArcGIS layer only exposes a
        # weekday name (PickupDay) with no date or week-parity field. When the
        # user supplies a known recycling date, project the fortnightly cadence
        # from it instead of returning the next occurrence of the weekday.
        if waste_type == "RECYCLE" and self._recycle_reference_date is not None:
            entries.append(
                Collection(
                    date=self._next_biweekly(self._recycle_reference_date, today),
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )
            return entries

        pickup_day = None
        for field_name in ("PickupDay", "PickUpDay", "PICKUPDAY"):
            value = attributes.get(field_name)
            if value:
                pickup_day = str(value).strip()
                break

        if pickup_day:
            next_date = self._resolve_pickup_date(pickup_day, today)
            entries.append(
                Collection(
                    date=next_date,
                    t=waste_type,
                    icon=ICON_MAP.get(waste_type),
                )
            )

        return entries

    def _next_weekday(self, weekday_name: str, today: date) -> date:
        target_weekday = WEEKDAY_INDEX[weekday_name.lower()]
        days_ahead = (target_weekday - today.weekday()) % 7
        return today + timedelta(days=days_ahead)

    def _next_biweekly(self, reference_date: date, today: date) -> date:
        """Return the next pickup on or after today on the same 14-day cycle as reference_date."""
        offset = (today - reference_date).days % 14
        if offset == 0:
            return today
        return today + timedelta(days=14 - offset)

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

        raise ValueError(
            f"Unable to calculate next '{nth}' '{weekday_name}' date from {today}."
        )

    def _resolve_pickup_date(self, pickup_rule: str, today: date) -> date:
        normalized_rule = pickup_rule.strip()
        normalized_rule_lower = normalized_rule.lower()

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

        raise ValueError(f"Unsupported pickup rule returned by API: '{pickup_rule}'")

    def _fetch_unofficial(self) -> list:
        """Fetch from the unofficial okc.schizo.dev API using a single recordID.

        The endpoint returns explicit upcoming dates for trash, recycling and
        bulky waste, so no weekday/biweekly reconstruction is required.
        """
        response = requests.get(
            UNOFFICIAL_URL,
            params={"recordID": self._record_id},
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        try:
            json_data = response.json()
        except ValueError as exc:
            raise SourceArgumentNotFound(
                "recordID",
                self._record_id,
                "the unofficial source did not return valid JSON for this recordID.",
            ) from exc

        if not isinstance(json_data, dict):
            raise SourceArgumentNotFound(
                "recordID",
                self._record_id,
                "no schedule found for this recordID in the unofficial source.",
            )

        today = datetime.now().date()
        entries: list = []

        def _next_from_pickups(pickups) -> date | None:
            for pickup in pickups or []:
                if not isinstance(pickup, dict):
                    continue
                raw = pickup.get("date")
                if not raw:
                    continue
                try:
                    parsed = datetime.strptime(str(raw), "%Y-%m-%d").date()
                except ValueError:
                    continue
                if parsed >= today:
                    return parsed
            return None

        # Trash: single "next" pickup, optionally falling back to the weekday.
        trash = json_data.get("trash")
        if isinstance(trash, dict):
            trash_date: date | None = None
            raw_next = (trash.get("next") or {}).get("date")
            if raw_next:
                try:
                    parsed = datetime.strptime(str(raw_next), "%Y-%m-%d").date()
                    if parsed >= today:
                        trash_date = parsed
                except ValueError:
                    trash_date = None
            if trash_date is None and trash.get("day"):
                trash_date = self._resolve_pickup_date(str(trash["day"]), today)
            if trash_date is not None:
                entries.append(
                    Collection(date=trash_date, t="TRASH", icon=ICON_MAP.get("TRASH"))
                )

        # Recycling: list of upcoming biweekly pickups.
        recycling = json_data.get("recycling")
        if isinstance(recycling, dict):
            recycle_date = _next_from_pickups(recycling.get("pickups"))
            if recycle_date is None and recycling.get("day"):
                recycle_date = self._resolve_pickup_date(str(recycling["day"]), today)
            if recycle_date is not None:
                entries.append(
                    Collection(
                        date=recycle_date, t="RECYCLE", icon=ICON_MAP.get("RECYCLE")
                    )
                )

        # Bulky waste: list of upcoming monthly pickups.
        bulky = json_data.get("bulkyWaste")
        if isinstance(bulky, dict):
            bulky_date = _next_from_pickups(bulky.get("pickups"))
            if bulky_date is None and bulky.get("schedule"):
                bulky_date = self._resolve_pickup_date(str(bulky["schedule"]), today)
            if bulky_date is not None:
                entries.append(
                    Collection(date=bulky_date, t="BULKY", icon=ICON_MAP.get("BULKY"))
                )

        if not entries:
            raise SourceArgumentNotFound(
                "recordID",
                self._record_id,
                "no upcoming collections found for this recordID in the unofficial source.",
            )

        return entries

    def _fetch_official(self) -> list:
        """Fetch from the official OKC Open Data Portal (ArcGIS FeatureServer)."""
        entries: list = []

        for waste_type, object_id in self._object_ids.items():
            if not object_id:
                continue
            layer_url, argument = WASTE_LAYERS[waste_type]
            attributes = self._query_object_id(layer_url, object_id, argument)
            entries.extend(self._parse_pickup_dates(attributes, waste_type))

        return entries

    def fetch(self):
        # Prefer the unofficial okc.schizo.dev API (single recordID, explicit
        # dates, most reliable feed). If it errors or returns nothing and
        # official OBJECTIDs are also configured, fall back to the official
        # ArcGIS zones automatically.
        has_official = any(self._object_ids.values())

        if self._record_id:
            try:
                entries = self._fetch_unofficial()
            except Exception:
                if not has_official:
                    raise
                entries = []
            if entries or not has_official:
                return entries

        return self._fetch_official()
