from datetime import date, datetime, timedelta
from typing import List, Dict
import re
import logging

import requests

# Set up logging for the module
_LOGGER = logging.getLogger(__name__)

# Try to import Collection from the expected environment.
try:
    from waste_collection_schedule import Collection
except ImportError:
    # MOCK CLASS
    class Collection:
        def __init__(self, date, t, icon):
            self.date = date
            self.t = t
            self.icon = icon
            self.note = ""

# --- COMPONENT METADATA ---
TITLE = "Community Waste Disposal (CWD)"
DESCRIPTION = "Source for Community Waste Disposal (CWD) in North Texas"
URL = "https://www.communitywastedisposal.com"
COUNTRY = "us"

TEST_CASES = {
    "Forney TX": {"address": "100 Princeton Cir, Forney, TX 75126"},
    "Allen TX": {"address": "123 Main St, Allen, TX 75002"},
}
# -------------------------------------


# Layer to Waste Type Mapping
LAYER_CONFIG = {
    0: {"type": "HHW", "icon": "mdi:delete-sweep"},
    1: {"type": "Recycling", "icon": "mdi:recycle"},
    2: {"type": "Trash", "icon": "mdi:trash-can-outline"},
    3: {"type": "Bulk Waste", "icon": "mdi:package-variant"},
    4: {"type": "Yard Waste", "icon": "mdi:leaf"},
    5: {"type": "Compost", "icon": "mdi:compost"},
}

WEEKDAY_MAP = {
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
    "Friday": 4, "Saturday": 5, "Sunday": 6,
}

class Source:
    def __init__(self, address: str):
        self.address = address.strip()
        self._lat: float | None = None
        self._lon: float | None = None
        self._community: str | None = None
        self._holidays: Dict[str, Dict[str, int]] = {}
        self._js_url: str | None = None

    # Get URL for main JS file
    def _get_main_js_url(self) -> str:
        """
        Fetches index.html to find the current version of the main.[hash].js file.
        """
        base_url = "https://support.newedgeservices.com/cwd/"
        headers = {"User-Agent": "hacs_waste_collection_schedule/1.0 (+https://github.com/mampfes/hacs_waste_collection_schedule)"}

        try:
            _LOGGER.debug(f"Fetching base HTML from {base_url} to find JS version.")
            r = requests.get(base_url, headers=headers, timeout=15)
            r.raise_for_status()
            html_content = r.text
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Failed to fetch index.html to determine JS URL: {e}")
            raise ValueError("Could not fetch the base application page.")

        # Regex to find the main.[hash].js link
        pattern = r'<script[^>]+src=["\'](/cwd/static/js/main\.[0-9a-f]+\.js)["\']'
        match = re.search(pattern, html_content)

        if not match:
            _LOGGER.error("Could not find the 'main.[hash].js' file path in index.html.")
            raise ValueError("Could not parse dynamic JavaScript URL from application index.")

        # Construct the full absolute URL
        relative_path = match.group(1)
        full_url = "https://support.newedgeservices.com" + relative_path

        _LOGGER.info(f"Dynamically resolved main JS URL: {full_url}")
        return full_url

    # Get content from main JS file
    def _fetch_main(self) -> str:

        if not self._js_url:
            self._js_url = self._get_main_js_url() # This will raise an error if it fails

        url = self._js_url
        headers = {"User-Agent": "hacs_waste_collection_schedule/1.0 (+https://github.com/mampfes/hacs_waste_collection_schedule)"}
        try:
            _LOGGER.debug(f"Fetching JS content from dynamic URL: {url}")
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            _LOGGER.debug("JS content fetched successfully.")
            return r.text
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Failed to fetch main JS file for holidays from {url}: {e}")
            raise # Re-raise to ensure calling function handles it


    def _get_holidays(self, target_city: str) -> None:
        _LOGGER.debug(f"Starting holiday lookup for community: {target_city}")
        try:
            js_content = self._fetch_main()
        except Exception:
            self._holidays = {}
            _LOGGER.warning("Skipping holiday processing due to failed JS fetch.")
            return

        escaped_name = re.escape(target_city)
        community_pattern = rf'["\']?{escaped_name}["\']?\s*:\s*\['
        community_match = re.search(community_pattern, js_content, re.IGNORECASE)

        if not community_match:
            self._holidays = {}
            _LOGGER.warning(f"Community '{target_city}' not found in JS data for holidays.")
            return

        search_start = community_match.start()
        search_end_match = re.search(r'\],', js_content[search_start:])
        if search_end_match:
            search_end = search_start + search_end_match.end()
        else:
            search_end = min(len(js_content), search_start + 50000)

        community_data = js_content[search_start:search_end]
        holidays_pattern = r'service\s*:\s*Rt\.HOLIDAYS\s*,\s*dates\s*:\s*\[([^\]]+)\]'
        holidays_match = re.search(holidays_pattern, community_data)

        if not holidays_match:
            self._holidays = {}
            _LOGGER.debug(f"Holiday section not found for {target_city}.")
            return

        holidays_section = holidays_match.group(1)
        holiday_pattern = r'start\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?end\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?skip\s*:\s*!([01])'
        matches = re.findall(holiday_pattern, holidays_section)

        holidays = {}

        for start_str, end_str, skip_flag in matches:
            skip = skip_flag == '1'
            delay = 1 if skip else 0

            try:
                parts = start_str.split('-')
                if len(parts) == 3:
                    start_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    continue
            except (ValueError, TypeError):
                continue

            end_date = start_date
            if end_str:
                try:
                    parts = end_str.split('-')
                    if len(parts) == 3:
                        parsed_end_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                        if parsed_end_date >= start_date:
                            end_date = parsed_end_date
                except (ValueError, TypeError):
                    pass

            name = "Holiday"
            current = start_date
            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                if delay > 0:
                    holidays[date_str] = {"name": name, "delay": delay}
                current += timedelta(days=1)

        self._holidays = holidays
        _LOGGER.info(f"Found {len(self._holidays)} holiday delay days for {target_city}.")

    def _geocode(self) -> None:
        if self._lat is not None:
            return

        params = {"q": self.address, "format": "json", "limit": 1, "addressdetails": 1}
        headers = {"User-Agent": "hacs_waste_collection_schedule/1.0 (+https://github.com/mampfes/hacs_waste_collection_schedule)"}
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Geocoding network request failed: {e}")
            raise ValueError(f"Geocoding failed due to network error.")

        if not data:
            _LOGGER.error(f"Geocoding returned no data for: {self.address}")
            raise ValueError(f"Address not found: '{self.address}'. Try a more specific address.")

        result = data[0]
        self._lat = float(result["lat"])
        self._lon = float(result["lon"])

        addr = result.get("address", {})
        community = addr.get("city") or addr.get("town") or addr.get("village") or ""

        if not community:
            _LOGGER.error("Community name could not be extracted from geocoding result.")
            raise ValueError(f"Could not determine community for address '{self.address}'.")
        self._community = community
        _LOGGER.info(f"Geocoding successful. Lat: {self._lat}, Lon: {self._lon}, Community: {self._community}")

    def fetch(self) -> List[Collection]:
        import datetime

        try:
            self._geocode()
        except ValueError as e:
            _LOGGER.error(f"Geocoding/Community lookup failed: {e}")
            raise

        self._get_holidays(self._community)

        base_url = "https://services3.arcgis.com/xeSJphIgrY4QfLVq/arcgis/rest/services/CWD_Routes_View/FeatureServer"
        entries: List[Collection] = []

        for layer_id, config in LAYER_CONFIG.items():
            query_url = (
                f"{base_url}/{layer_id}/query?"
                f"f=json&where=1%3D1&outFields=*&"
                f"geometry={self._lon}%2C{self._lat}&"
                f"geometryType=esriGeometryPoint&"
                f"spatialRel=esriSpatialRelWithin&"
                f"returnGeometry=false&inSR=4326&outSR=4326"
            )

            try:
                _LOGGER.debug(f"Querying ArcGIS Layer {layer_id} ({config['type']})")
                r = requests.get(query_url, timeout=10)
                r.raise_for_status()
                data = r.json()

                if not data.get("features"):
                    _LOGGER.debug(f"Layer {layer_id} returned no features.")
                    continue

                attrs = data["features"][0]["attributes"]

                day1 = attrs.get("PickupDay1")
                day2 = attrs.get("PickupDay2")

                def is_valid_day(d):
                    if not d or not isinstance(d, str): return False
                    d = d.strip()
                    return d in WEEKDAY_MAP and d.lower() not in ["na", "none", "null"]

                pickup_days = []
                if is_valid_day(day1): pickup_days.append(day1.strip())
                if day2 and is_valid_day(day2): pickup_days.append(day2.strip())

                if not pickup_days: continue

                frequency = str(attrs.get("Frequency", "Weekly")).lower()
                timing_week = str(attrs.get("TimingWeek", "")).lower()

                today = datetime.date.today()
                end_date = today + timedelta(days=365)

                for day_name in pickup_days:
                    if day_name not in WEEKDAY_MAP: continue

                    weekday = WEEKDAY_MAP[day_name]

                    # --- DATE GENERATION START ---
                    days_ahead = (weekday - today.weekday()) % 7
                    current_date = today + timedelta(days=days_ahead)

                    interval = 7
                    is_first_day = "1st" in day_name or "1st" in timing_week
                    if is_first_day:
                        next_month = today.replace(day=28) + timedelta(days=4)
                        current_date = date(next_month.year, next_month.month, 1)
                        days_ahead = (weekday - current_date.weekday()) % 7
                        current_date += timedelta(days=days_ahead)
                        if current_date < today:
                            next_month = current_date.replace(day=28) + timedelta(days=4)
                            current_date = date(next_month.year, next_month.month, 1)
                            days_ahead = (weekday - current_date.weekday()) % 7
                            current_date += timedelta(days=days_ahead)
                        interval = 30
                    elif "biweekly" in frequency:
                        interval = 7

                    while current_date <= end_date:
                        original_date = current_date
                        date_str = current_date.strftime("%Y-%m-%d")
                        note = ""

                        # --- HOLIDAY DELAY LOGIC ---
                        if date_str in self._holidays:
                            delay_info = self._holidays[date_str]
                            current_date += timedelta(days=delay_info["delay"])
                            note = f"HOLIDAY DELAY: {delay_info['name']} -> +{delay_info['delay']} day"
                        # --- END HOLIDAY DELAY LOGIC ---

                        # --- COLLECTION OBJECT CREATION ---
                        entry = Collection(
                            date=current_date, t=config["type"], icon=config["icon"]
                        )

                        if "biweekly" in frequency:
                            week_num = original_date.isocalendar()[1] % 2
                            if week_num == 1:
                                entries.append(entry)
                        else:
                            entries.append(entry)

                        if "biweekly" in frequency:
                            current_date = original_date + timedelta(days=7)
                        elif is_first_day:
                            next_month = original_date.replace(day=28) + timedelta(days=4)
                            current_date = date(next_month.year, next_month.month, 1)
                            days_ahead = (weekday - current_date.weekday()) % 7
                            current_date += timedelta(days=days_ahead)
                        else:
                            current_date = original_date + timedelta(days=interval)
                    # --- DATE GENERATION END ---

            except requests.exceptions.RequestException as e:
                _LOGGER.error(f"ArcGIS Layer {layer_id} network request failed: {e}")
                continue
            except Exception as e:
                _LOGGER.error(f"ArcGIS Layer {layer_id} parsing failed: {e}")
                continue

        # Final check
        if not entries:
            _LOGGER.warning(f"Final collection list is empty after checking all layers.")
            raise ValueError(
                f"No valid pickup schedule found for '{self.address}'. "
                "Verify the address on [CWD View My Schedule](https://www.communitywastedisposal.com/view-my-schedule/)."
            )

        _LOGGER.info(f"Successfully generated {len(entries)} collection entries.")
        return entries