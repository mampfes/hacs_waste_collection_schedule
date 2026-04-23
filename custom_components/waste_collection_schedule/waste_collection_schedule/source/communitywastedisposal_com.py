import json
import logging
import re
from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import (
    ArcGisError,
    query_feature_layer,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Community Waste Disposal (CWD)"
DESCRIPTION = "Source for Community Waste Disposal (CWD) in North Texas"
URL = "https://www.communitywastedisposal.com"
COUNTRY = "us"

TEST_CASES = {
    "Forney TX": {"address": "100 Princeton Cir, Forney, TX 75126"},
    "Allen TX": {"address": "123 Main St, Allen, TX 75002"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address including city and ZIP (e.g. '123 Main St, Allen, TX 75002')",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "address": "Street Address",
    },
}

LAYER_CONFIG = {
    0: {"type": "HHW", "icon": "mdi:delete-sweep"},
    1: {"type": "Recycling", "icon": "mdi:recycle"},
    2: {"type": "Trash", "icon": "mdi:trash-can-outline"},
    3: {"type": "Bulk Waste", "icon": "mdi:package-variant"},
    4: {"type": "Yard Waste", "icon": "mdi:leaf"},
    5: {"type": "Compost", "icon": "mdi:compost"},
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

STR_TO_WEEKDAY = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

FEATURE_BASE = "https://services3.arcgis.com/xeSJphIgrY4QfLVq/arcgis/rest/services/CWD_Routes_View/FeatureServer"
GEOCODE_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer"


class Source:
    def __init__(self, address: str):
        self._address = address.strip()

    def _geocode(self) -> tuple[dict, str]:
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

    def _generate_dates(
        self,
        day_name: str,
        frequency: str,
        timing_week: str,
        start_date: date,
        end_date: date,
        holidays: dict[str, dict[str, int]],
    ) -> list[date]:
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

    def fetch(self) -> list[Collection]:
        try:
            location, community = self._geocode()
        except SourceArgumentNotFound:
            raise
        except Exception as e:
            raise SourceArgumentNotFound("address", self._address) from e

        holidays = self._get_holidays(community) if community else {}

        today = date.today()
        end_date = today + timedelta(days=365)
        entries: list[Collection] = []

        for layer_id, config in LAYER_CONFIG.items():
            layer_url = f"{FEATURE_BASE}/{layer_id}"
            try:
                features = query_feature_layer(layer_url, geometry=location)
            except ArcGisError:
                continue

            attrs = features[0]
            pickup_days = [
                d.strip()
                for key in ("PickupDay1", "PickupDay2")
                if (d := attrs.get(key))
                and isinstance(d, str)
                and d.strip() in STR_TO_WEEKDAY
            ]
            if not pickup_days:
                continue

            frequency = str(attrs.get("Frequency", "Weekly")).lower()
            timing_week = str(attrs.get("TimingWeek", "")).lower()

            for day_name in pickup_days:
                for collection_date in self._generate_dates(
                    day_name, frequency, timing_week, today, end_date, holidays
                ):
                    entries.append(
                        Collection(
                            date=collection_date,
                            t=config["type"],
                            icon=config["icon"],
                        )
                    )

        if not entries:
            raise SourceArgumentNotFound("address", self._address)

        return entries
