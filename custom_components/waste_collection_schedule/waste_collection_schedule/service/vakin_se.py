import json
import re
from datetime import datetime, timedelta

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "Vakin"
DESCRIPTION = (
    "Source for Vakin waste collection (Umeå, Nordmaling, and Vindeln), Sweden."
)
URL = "https://www.vakin.se"
COUNTRY = "se"
EXTRA_INFO = [
    {
        "title": "Umeå",
        "url": "https://www.vakin.se",
        "default": True,
    },
    {"title": "Nordmaling", "url": "https://www.vakin.se"},
    {"title": "Vindeln", "url": "https://www.vakin.se"},
]
TEST_CASES = {
    "Kajakvägen 3, Täfteå": {"address": "Kajakvägen 3, Täfteå"},
    "Kajakvägen 3": {"address": "Kajakvägen 3"},
    "Storgatan 1, Umeå": {"address": "Storgatan 1, Umeå", "city": "Umeå"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your street name and house number, e.g. 'Kajakvägen 3' or 'Kajakvägen 3, Täfteå'. Optionally specify the city if there are ambiguous matches across municipalities.",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": "Street address with house number (e.g. 'Kajakvägen 3' or 'Kajakvägen 3, Täfteå')",
        "city": "City / postal locality (optional, e.g. 'Täfteå', 'Umeå', 'Nordmaling')",
    },
}

WASTE_PAGE_URL = (
    "https://www.vakin.se/kundserviceochetjanster/sophamtning/"
    "narkommersopbilen.4.6252338c1a0c6bd088ed01f.html"
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

PORTLET_ID_PATTERN = re.compile(
    r"applicationId:\s*['\"]se\.soleil\.garbageTruckFetcher[^'\"]*['\"].*?"
    r"portletId:\s*['\"]([^'\"]+)['\"]"
)
PAGE_ID_PATTERN = re.compile(r"pageId:\s*['\"]([^'\"]+)['\"]")

FALLBACK_PAGE_ID = "4.6252338c1a0c6bd088ed01f"
FALLBACK_PORTLET_ID = "12.6252338c1a0c6bd088ed033"

ICON_MAP = {
    "Matavfall": Icons.BIO_KITCHEN,
    "Restavfall": Icons.GENERAL_WASTE,
    "Pappersförpackningar": Icons.PAPER,
    "Plastförpackningar": Icons.PLASTIC_PACKAGING,
    "Fett": Icons.BIO_KITCHEN,
}


def _resolve_endpoints(session: requests.Session) -> tuple[str, str]:
    """Resolve getAddresses and getcontainerdata endpoints from the live waste page."""
    try:
        r = session.get(WASTE_PAGE_URL, headers=DEFAULT_HEADERS, timeout=30)
        r.raise_for_status()
        html = r.text

        portlet_match = PORTLET_ID_PATTERN.search(html)
        page_match = PAGE_ID_PATTERN.search(html)

        page_id = page_match.group(1) if page_match else FALLBACK_PAGE_ID
        portlet_id = portlet_match.group(1) if portlet_match else FALLBACK_PORTLET_ID
    except Exception:
        page_id = FALLBACK_PAGE_ID
        portlet_id = FALLBACK_PORTLET_ID

    base = f"https://www.vakin.se/appresource/{page_id}/{portlet_id}"
    return f"{base}/getAddresses", f"{base}/getcontainerdata"


class Source:
    def __init__(self, address: str, city: str | None = None):
        if not address:
            raise SourceArgumentRequired(
                "address",
                "an address is required to fetch the collection schedule",
            )
        self._address = address.strip()
        self._city = city.strip() if city else None

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        search_endpoint, schedule_endpoint = _resolve_endpoints(session)

        # 1. Search for address
        params = {"pickupAddress": self._address}
        r = session.get(search_endpoint, params=params, timeout=30)
        r.raise_for_status()

        data = r.json()
        addresses = data.get("data", [])

        if not addresses:
            # If the user included postal code or city, try stripping to just street + number
            clean_search = re.sub(r",?\s*\b\d{5}\b", "", self._address).strip()
            if clean_search != self._address:
                r = session.get(
                    search_endpoint, params={"pickupAddress": clean_search}, timeout=30
                )
                r.raise_for_status()
                addresses = r.json().get("data", [])

        if not addresses:
            raise SourceArgumentNotFound("address", self._address)

        selected = None
        if len(addresses) == 1:
            selected = addresses[0]
        elif self._city:
            for item in addresses:
                city_val = item.get("value", {}).get("city", "")
                label_val = item.get("label", "")
                if (
                    self._city.lower() in city_val.lower()
                    or self._city.lower() in label_val.lower()
                ):
                    selected = item
                    break

        if not selected:
            # Check for exact street address match (case-insensitive)
            addr_lower = self._address.lower()
            for item in addresses:
                label_lower = item.get("label", "").lower()
                address_val_lower = item.get("value", {}).get("address", "").lower()
                if addr_lower in (label_lower, address_val_lower):
                    selected = item
                    break

        if not selected:
            # If still ambiguous, offer suggestions
            suggestions = [item.get("label", "") for item in addresses[:10]]
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                suggestions,
            )

        address_param = selected.get("value")
        today = datetime.now().date()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=365)).strftime("%Y-%m-%d")

        r_sched = session.get(
            schedule_endpoint,
            params={
                "addressParams": json.dumps(address_param),
                "startDate": start_date,
                "endDate": end_date,
            },
            timeout=30,
        )
        r_sched.raise_for_status()

        schedule_data = r_sched.json()
        if not isinstance(schedule_data, list):
            raise ValueError("Unexpected response format from Vakin (expected a list)")

        entries = []
        for event in schedule_data:
            date_str = event.get("executionDate")
            if not date_str:
                continue
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            content_types = event.get("contentTypes", [])

            for waste_type in content_types:
                entries.append(
                    Collection(
                        date=date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        return entries
