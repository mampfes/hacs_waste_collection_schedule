import json
import logging
import re
from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service import ArcGis
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    RECYCLABLES,
)

# CWD (North Texas) publishes pickup days/frequency per service across SIX ArcGIS
# FeatureServer layers, queried with a single spatial point each. The point is
# resolved with a *custom* GeocodeServer call that also returns the City, which
# drives a holiday-delay lookup scraped from the support portal's bundled JS.
#
# This source keeps its own retrieve() because it: (1) geocodes via a custom URL
# returning (location, community); (2) queries multiple layers; (3) fetches
# holiday delays. retrieve() does acquisition only (raw ArcGis.feature_query
# Responses per layer); parse() extracts attrs per layer and skips empties; the
# week/holiday date arithmetic stays in _describe (count=1 one-off Schedules so
# the exact legacy dates, including holiday shifts, are reproduced).

_LOGGER = logging.getLogger(__name__)

FEATURE_BASE = "https://services3.arcgis.com/xeSJphIgrY4QfLVq/arcgis/rest/services/CWD_Routes_View/FeatureServer"
GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"

# Layer id -> legacy raw ``t=`` string (the key into _TYPE_MAP below).
LAYER_TYPES = {
    0: "HHW",
    1: "Recycling",
    2: "Trash",
    3: "Bulk Waste",
    4: "Yard Waste",
    5: "Compost",
}

_TYPE_MAP = {
    "HHW": HAZARDOUS,
    "Recycling": RECYCLABLES,
    "Trash": GENERAL_WASTE,
    "Bulk Waste": BULKY_WASTE,
    "Yard Waste": GARDEN_WASTE,
    "Compost": ORGANIC,
}

WEEKDAY_MAP = {
    "Monday": MO,
    "Tuesday": TU,
    "Wednesday": WE,
    "Thursday": TH,
    "Friday": FR,
    "Saturday": SA,
    "Sunday": SU,
}


def _generate_dates(
    day_name: str,
    frequency: str,
    timing_week: str,
    start_date: date,
    end_date: date,
    holidays: dict[str, dict[str, int]],
) -> list[date]:
    """Project a recurring pickup day into concrete dates (legacy arithmetic)."""
    weekday = WEEKDAY_MAP.get(day_name)
    if not weekday:
        return []

    rule = rrule(
        WEEKLY,
        byweekday=weekday,
        dtstart=datetime.combine(start_date, datetime.min.time()),
        until=datetime.combine(end_date, datetime.min.time()),
    )
    all_dates = [d.date() for d in rule]

    if "1st" in timing_week:
        dates = [d for d in all_dates if d.day <= 7]
    elif "biweekly" in frequency:
        dates = [d for i, d in enumerate(all_dates) if d.isocalendar()[1] % 2 == 1]
    else:
        dates = all_dates

    return [
        (
            d + timedelta(days=holidays[d.strftime("%Y-%m-%d")]["delay"])
            if d.strftime("%Y-%m-%d") in holidays
            else d
        )
        for d in dates
    ]


def _describe(record, source):
    """Yield one ``count=1`` Schedule per concrete pickup date for a layer."""
    attrs = record["attrs"]
    raw_type = record["type"]

    pickup_days = [
        d.strip()
        for key in ("PickupDay1", "PickupDay2")
        if (d := attrs.get(key))
        and isinstance(d, str)
        and recurrence.weekday(d.strip()) is not None
    ]
    if not pickup_days:
        return

    frequency = str(attrs.get("Frequency", "Weekly")).lower()
    timing_week = str(attrs.get("TimingWeek", "")).lower()

    for day_name in pickup_days:
        for collection_date in _generate_dates(
            day_name,
            frequency,
            timing_week,
            source._today,
            source._end_date,
            source._holidays,
        ):
            yield Schedule(raw_type, collection_date, count=1)


class Source(BaseSource):
    TITLE = "Community Waste Disposal (CWD)"
    DESCRIPTION = "Source for Community Waste Disposal (CWD) in North Texas"
    URL = "https://www.communitywastedisposal.com"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Forney TX": {"address": "100 Princeton Cir, Forney, TX 75126"},
        "Allen TX": {"address": "123 Main St, Allen, TX 75002"},
    }

    PARAMS = [text_field("address", "Street Address")]

    HOWTO = {
        "en": (
            "Enter your street address including city and ZIP "
            "(e.g. '123 Main St, Allen, TX 75002')."
        ),
    }

    preprocessor = RecurrenceExpander(_describe)
    transformer = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)
        self._address = address.strip()
        self._holidays: dict[str, dict[str, int]] = {}
        self._today = date.today()
        self._end_date = self._today + timedelta(days=365)

    def _geocode(self) -> tuple[dict, str]:
        """Custom GeocodeServer call returning (location, community/City)."""
        r = requests.get(
            f"{GEOCODE_URL}/findAddressCandidates",
            params={
                "SingleLine": self._address,
                "outSR": json.dumps({"wkid": 4326}),
                "maxLocations": 1,
                "outFields": "City",
                "f": "json",
            },
            timeout=20,
        )
        r.raise_for_status()
        candidates = r.json().get("candidates", [])
        if not candidates:
            raise SourceArgumentNotFound("address", self._address)
        location = candidates[0]["location"]
        city = candidates[0].get("attributes", {}).get("City", "")
        return location, city

    def _get_holidays(self, community: str) -> dict[str, dict[str, int]]:
        try:
            base_url = "https://support.newedgeservices.com/cwd/"
            r = requests.get(base_url, timeout=15)
            r.raise_for_status()
            match = re.search(
                r'<script[^>]+src=["\'](/cwd/static/js/main\.[0-9a-f]+\.js)["\']',
                r.text,
            )
            if not match:
                return {}
            js_url = "https://support.newedgeservices.com" + match.group(1)
            r = requests.get(js_url, timeout=15)
            r.raise_for_status()
            js_content = r.text
        except requests.RequestException:
            return {}

        escaped = re.escape(community)
        cm = re.search(rf'["\']?{escaped}["\']?\s*:\s*\[', js_content, re.IGNORECASE)
        if not cm:
            return {}

        start = cm.start()
        end_m = re.search(r"\],", js_content[start:])
        end = start + end_m.end() if end_m else min(len(js_content), start + 50000)
        segment = js_content[start:end]

        hm = re.search(
            r"service\s*:\s*Rt\.HOLIDAYS\s*,\s*dates\s*:\s*\[([^\]]+)\]", segment
        )
        if not hm:
            return {}

        holidays: dict[str, dict[str, int]] = {}
        for start_str, end_str, skip_flag in re.findall(
            r'start\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?end\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?skip\s*:\s*!([01])',
            hm.group(1),
        ):
            delay = 1 if skip_flag == "1" else 0
            if not delay:
                continue
            try:
                parts = start_str.split("-")
                start_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, TypeError, IndexError):
                continue
            end_date = start_date
            if end_str:
                try:
                    parts = end_str.split("-")
                    parsed = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    if parsed >= start_date:
                        end_date = parsed
                except (ValueError, TypeError, IndexError):
                    pass
            current = start_date
            while current <= end_date:
                holidays[current.strftime("%Y-%m-%d")] = {"delay": delay}
                current += timedelta(days=1)

        return holidays

    def retrieve(self, source):
        """Geocode (custom), look up holidays, then query each layer (raw)."""
        try:
            location, community = self._geocode()
        except SourceArgumentNotFound:
            raise
        except Exception as e:
            raise SourceArgumentNotFound("address", self._address) from e

        self._holidays = self._get_holidays(community) if community else {}

        responses = []
        for layer_id, raw_type in LAYER_TYPES.items():
            layer_url = f"{FEATURE_BASE}/{layer_id}"
            try:
                response = ArcGis.feature_query(layer_url, geometry=location)
            except Exception:
                continue
            responses.append((raw_type, response))
        return responses

    def parse(self, raw, source):
        """Extract the first feature's attributes per layer; skip empties."""
        records = []
        for raw_type, response in raw:
            try:
                response.raise_for_status()
                features = response.json().get("features", [])
            except Exception:
                continue
            if not features:
                continue
            attrs = features[0].get("attributes", {})
            records.append({"type": raw_type, "attrs": attrs})
        return records
