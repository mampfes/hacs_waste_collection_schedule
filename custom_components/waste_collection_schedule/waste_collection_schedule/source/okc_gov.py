import re
from datetime import date, datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "City of Oklahoma City"
DESCRIPTION = "Source for the City of Oklahoma City Open Data Portal (ArcGIS) waste collection zones."
URL = "https://www.okc.gov"
COUNTRY = "us"
TEST_CASES = {
    "Trash Fri / Recycle Mon / Bulky 4th Mon": {
        "trashObjectID": 1,
        "recycleObjectID": 1215,
        "bulkyObjectID": 1,
    },
    "Recycle every other week (anchored)": {
        "recycleObjectID": 1215,
        "recycle_reference_date": "2026-06-15",
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
        "trashObjectID": "OBJECTID of your trash collection zone from the OKC Open Data Portal.",
        "recycleObjectID": "OBJECTID of your recycling zone from the OKC Open Data Portal.",
        "bulkyObjectID": "OBJECTID of your bulky waste zone from the OKC Open Data Portal.",
        "recycle_reference_date": "Optional ISO date (YYYY-MM-DD) of a known recycling collection. OKC recycling runs every other week, but the data portal only exposes a weekday; provide one real pickup date so the alternating-week schedule can be calculated correctly.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Provide the OBJECTID of one or more of your collection zones from the OKC Open "
    "Data Portal (trashObjectID, recycleObjectID, bulkyObjectID). At least one is required. "
    "Open the FeatureServer layers linked in the documentation, use the Query page to locate "
    "the zone that covers your address, and read its OBJECTID. Recycling is collected every "
    "other week and the portal only reports the weekday, so also set recycle_reference_date "
    "to one date you know recycling was (or will be) collected to pin the correct week."
}


class Source:
    def __init__(
        self,
        trashObjectID: str | int = "",
        recycleObjectID: str | int = "",
        bulkyObjectID: str | int = "",
        recycle_reference_date: str = "",
    ):
        self._record_ids = {
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

        if not any(self._record_ids.values()):
            raise SourceArgumentNotFound(
                "trashObjectID",
                "",
                "provide at least one of trashObjectID, recycleObjectID or bulkyObjectID.",
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

    def fetch(self):
        entries: list = []

        for waste_type, object_id in self._record_ids.items():
            if not object_id:
                continue
            layer_url, argument = WASTE_LAYERS[waste_type]
            attributes = self._query_object_id(layer_url, object_id, argument)
            entries.extend(self._parse_pickup_dates(attributes, waste_type))

        return entries
