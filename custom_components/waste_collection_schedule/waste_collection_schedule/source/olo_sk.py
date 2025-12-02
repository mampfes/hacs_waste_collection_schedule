import datetime
import re
from typing import Any

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentRequired

TITLE = "OLO"
DESCRIPTION = "Source for OLO in Bratislava, Slovakia"
URL = "https://www.olo.sk"
TEST_CASES = {
    "Jantarova 47": {"street": "Jantarova 47", "registrationNumber": "1440381"},
    "Jasovska 8": {"street": "Jasovska 8", "registrationNumber": "1353013"},
    "Rovniankova 5": {"street": "Rovniankova 5", "registrationNumber": ""},
}

# Waste types from OLO website with display names and icons
WASTE_TYPES = {
    "Zmiešaný odpad": ("Zmesový komunálny odpad", "mdi:trash-can"),
    "KBRO": ("Kuchynský bioodpad", "mdi:food-apple"),
    "BRO": ("Záhradný bioodpad", "mdi:leaf"),
    "Plast": ("Plast, kovy a nápojové kartóny", "mdi:bottle-soda"),
    "Papier": ("Papier", "mdi:newspaper"),
    "Sklo": ("Sklo", "mdi:bottle-wine"),
}

API_URL = "https://olo-strapi-meilisearch.bratislava.sk/indexes/pickup-day/search"

# Where to look for the API key
API_KEY_REGEX = r'"NEXT_PUBLIC_MEILISEARCH_HOST:",\s*".*?",\s*"(.*?)"'
API_KEY_SOURCE = "https://www.olo.sk/odpad/zistite-si-svoj-odvozovy-den"
API_KEY_JS_BASE = "https://www.olo.sk"
# Fallback API key in case we can't extract it from the source
API_KEY_FALLBACK = "ae84ae0982c2162a81eb253765ceaa8593abd9105c71954cf5c9620b0178cbb6"

# ### Arguments affecting the configuration GUI ####

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street name and number",
        "registrationNumber": "OLO registration number",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Enter street name",
        "registrationNumber": "Enter OLO registration number",
    }
}

# ### End of arguments affecting the configuration GUI ####


class Source:
    def __init__(self, street: str, registrationNumber: str = ""):
        self._street = street
        self._registrationNumber = registrationNumber

    def _find_api_key(self) -> str:
        """Find API key in the web page source code."""
        try:
            response = requests.get(API_KEY_SOURCE, timeout=10)
            response.raise_for_status()
            page_text = response.text

            # Find all .js references in the html source
            js_refs = re.findall(r'<script src="([^"]+)"', page_text)

            for js_ref in js_refs:
                api_key = self._parse_api_key(js_ref)
                if api_key:
                    return api_key
        except requests.RequestException:
            pass
        return ""

    def _parse_api_key(self, js_ref: str) -> str:
        """Extract the API key from a .js file."""
        try:
            response = requests.get(API_KEY_JS_BASE + js_ref, timeout=10)
            response.raise_for_status()
            js_source = response.text

            match = re.search(API_KEY_REGEX, js_source)
            if match:
                return match.group(1)
        except requests.RequestException:
            pass
        return ""

    def _fetch_pickup_days(self) -> list[dict[str, Any]]:
        """Fetch all pickup days for the given address."""
        api_key = self._find_api_key() or API_KEY_FALLBACK

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "authorization": f"Bearer {api_key}",
        }

        params = {
            "q": self._street,
            "limit": 100,
            "offset": 0,
            "filter": ['type = "pickup-day"'],
            "sort": ["pickup-day.address:asc"],
            "attributesToSearchOn": ["pickup-day.address"],
        }

        response = requests.post(API_URL, json=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        items = data.get("hits", [])
        return [item.get("pickup-day", {}) for item in items if item.get("pickup-day")]

    def _parse_frequency(self, frequency: str) -> list[tuple[int | None, int | None]]:
        """
        Parse frequency string like "[4,4]" or "[14,14];[1,1]".

        Returns list of tuples (even_week_day, odd_week_day) where:
        - Numbers 1-7 are ISO weekdays (1=Monday...7=Sunday)
        - None means no pickup that week
        """
        patterns = []
        # Split by semicolon for multiple seasonal patterns
        for part in frequency.split(";"):
            part = part.strip()
            # Extract numbers and dashes from brackets like "[4,4]" or "[-,5]"
            match = re.match(r"\[([^,]+),([^\]]+)\]", part)
            if match:
                even_str, odd_str = match.groups()
                even_day = int(even_str) if even_str.strip().isdigit() else None
                odd_day = int(odd_str) if odd_str.strip().isdigit() else None
                patterns.append((even_day, odd_day))
        return patterns

    def _parse_season(self, season_str: str | None) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """
        Parse season string like "01/04-31/10, 01/11-31/03".

        Returns list of ((start_day, start_month), (end_day, end_month)) tuples.
        """
        if not season_str:
            return []

        seasons = []
        for part in season_str.split(","):
            part = part.strip()
            match = re.match(r"(\d{2})/(\d{2})-(\d{2})/(\d{2})", part)
            if match:
                start_day, start_month, end_day, end_month = map(int, match.groups())
                seasons.append(((start_day, start_month), (end_day, end_month)))
        return seasons

    def _is_date_in_season(
        self, date: datetime.date, season: tuple[tuple[int, int], tuple[int, int]]
    ) -> bool:
        """Check if a date falls within a season range."""
        (start_day, start_month), (end_day, end_month) = season

        # Create date objects for comparison (use the date's year)
        year = date.year
        start_date = datetime.date(year, start_month, start_day)
        end_date = datetime.date(year, end_month, end_day)

        # Handle seasons that span year boundary (e.g., 01/12-27/02)
        if end_date < start_date:
            # Season spans year boundary
            return date >= start_date or date <= end_date
        else:
            return start_date <= date <= end_date

    def _generate_dates(
        self,
        frequency_patterns: list[tuple[int | None, int | None]],
        seasons: list[tuple[tuple[int, int], tuple[int, int]]],
    ) -> list[datetime.date]:
        """Generate collection dates for the next 90 days based on frequency patterns."""
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=90)
        dates = []

        current_date = today
        while current_date <= end_date:
            week_number = current_date.isocalendar()[1]
            is_even_week = week_number % 2 == 0
            weekday = current_date.isoweekday()  # 1=Monday...7=Sunday

            # Determine which frequency pattern to use based on season
            if seasons and len(frequency_patterns) == len(seasons):
                # Multiple patterns correspond to seasons
                for i, season in enumerate(seasons):
                    if self._is_date_in_season(current_date, season):
                        even_day, odd_day = frequency_patterns[i]
                        break
                else:
                    # Date not in any season, skip
                    current_date += datetime.timedelta(days=1)
                    continue
            elif frequency_patterns:
                # Single pattern, no seasons
                even_day, odd_day = frequency_patterns[0]
            else:
                current_date += datetime.timedelta(days=1)
                continue

            # Check if this weekday matches the pattern
            if is_even_week and even_day == weekday:
                dates.append(current_date)
            elif not is_even_week and odd_day == weekday:
                dates.append(current_date)

            current_date += datetime.timedelta(days=1)

        return dates

    def fetch(self) -> list[Collection]:
        if not self._street:
            raise SourceArgumentRequired("street")

        pickup_days = self._fetch_pickup_days()

        # Filter by registration number if provided
        if self._registrationNumber:
            pickup_days = [
                item
                for item in pickup_days
                if item.get("registrationNumber") == self._registrationNumber
            ]

        if not pickup_days:
            raise Exception("No waste data found for the given address")

        entries: list[Collection] = []
        seen: set[tuple[str, datetime.date]] = set()

        for item in pickup_days:
            waste_type = item.get("wasteType")
            if not waste_type:
                continue

            # Use known waste type info, or fall back to defaults for future-proofing
            if waste_type in WASTE_TYPES:
                display_name, icon = WASTE_TYPES[waste_type]
            else:
                # Default: use the API waste type name and a generic icon
                display_name = waste_type
                icon = "mdi:trash-can-outline"
            frequency = item.get("frequency", "")
            frequency_season = item.get("frequencySeason")

            if not frequency:
                continue

            frequency_patterns = self._parse_frequency(frequency)
            seasons = self._parse_season(frequency_season)
            dates = self._generate_dates(frequency_patterns, seasons)

            for date in dates:
                # Avoid duplicate entries
                key = (waste_type, date)
                if key not in seen:
                    seen.add(key)
                    entries.append(Collection(date=date, t=display_name, icon=icon))

        if not entries:
            raise Exception("No waste collection dates found")

        return sorted(entries, key=lambda x: x.date)
