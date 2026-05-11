import hashlib
import logging
from base64 import b64encode
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Gänserndorf City / Gänserndorf App"
DESCRIPTION = (
    "Source for waste collection schedule for the city of Gänserndorf, Austria. "
    "Uses the Jolioo mobile app API."
)
URL = "https://www.gaenserndorf.at/"
COUNTRY = "at"
EXTRA_INFO = [
    {
        "title": "Gänserndorf",
        "url": "https://www.gaenserndorf.at/",
        "country": "at",
    },
]
TEST_CASES = {
    "Baumschulweg": {"street": "Baumschulweg"},
    "Ahornweg": {"street": "Ahornweg"},
    "Siebenbrunner Straße (first calendar)": {
        "street": "Siebenbrunner Straße",
        "calendar_index": 0,
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Name",
        "calendar_index": "Calendar Index",
    },
    "de": {
        "street": "Straßenname",
        "calendar_index": "Kalender-Index",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "The name of your street as shown in the Gänserndorf App.",
        "calendar_index": "Index of the calendar to use when a street maps to multiple calendars (starting at 0).",
    },
    "de": {
        "street": "Der Straßenname, wie er in der Gänserndorf-App angezeigt wird.",
        "calendar_index": "Index des zu verwendenden Kalenders, wenn eine Straße mehreren Kalendern zugeordnet ist (beginnt bei 0).",
    },
}

# ────────────────── API credentials ──────────────────
_API_URL = "https://app.jolioo.com/api/mobile-app/"
_API_KEY = "e74b7a2955428b2ab520"
_API_SECRET = "3646728f96cf464aff7e"
_API_USERNAME = "mopedshop"
_API_PASSWORD = "T4P4qSur"
_USER_AGENT = f"JoliooMobileApp-{_API_KEY}"


def _basic_auth() -> str:
    """Return the Basic-Auth header value."""
    raw = f"{_API_USERNAME}:{_API_PASSWORD}"
    return "Basic " + b64encode(raw.encode()).decode()


def _api_hash(endpoint_path: str, body: str) -> str:
    """Compute the APIHASH exactly as the app does (no user token)."""
    hash_input = f"{_API_SECRET}@{endpoint_path}@{body}"
    return hashlib.sha1(hash_input.encode()).hexdigest()


def _post(endpoint: str, params: dict) -> dict:
    """Send an authenticated POST to the API and return parsed JSON."""
    body = "&".join(f"{k}={v}" for k, v in params.items())
    endpoint_path = f"api/mobile-app/{endpoint}"
    apihash = _api_hash(endpoint_path, body)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "APIHASH": apihash,
        "APIKEY": _API_KEY,
        "VERSION": "1",
        "Authorization": _basic_auth(),
        "User-Agent": _USER_AGENT,
    }

    resp = requests.post(
        f"{_API_URL}{endpoint}", headers=headers, data=body, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Jolioo API returned error for {endpoint}: {data}")

    return data["data"]


class Source:
    """Waste collection schedule source for Jolioo / Gänserndorf App."""

    def __init__(self, street: str, calendar_index: int = 0):
        self._street = street
        self._calendar_index = calendar_index

    def fetch(self):
        """Fetch the waste collection schedule."""

        # Step 1: get streets + calendars index
        index_data = _post(
            "garbagecalendarindexwithstreets",
            {"language": "de", "garbage_calendar_id": "1"},
        )

        streets = index_data.get("street_structure", [])

        # find the requested street (case-insensitive)
        match = None
        for s in streets:
            if s["garbage_calendar_street"].lower() == self._street.lower():
                match = s
                break

        if match is None:
            available = sorted(s["garbage_calendar_street"] for s in streets)
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, available
            )

        cal_ids = match["garbage_calendars_available"]
        if self._calendar_index >= len(cal_ids):
            raise SourceArgumentNotFoundWithSuggestions(
                "calendar_index",
                self._calendar_index,
                list(range(len(cal_ids))),
            )

        calendar_id = cal_ids[self._calendar_index]
        _LOGGER.debug(
            "Fetching garbage calendar %s for street '%s'",
            calendar_id,
            self._street,
        )

        # Step 2: fetch the actual dates for this calendar
        cal_data = _post(
            "garbagecalendar",
            {"language": "de", "garbage_calendar_id": str(calendar_id)},
        )

        # build a label-id → title lookup (only child labels that have a
        # garbage_label_label field, i.e. the ones that actually appear on items)
        labels = {}
        for lbl in cal_data.get("labels", []):
            if lbl.get("garbage_label_id_parent") is not None:
                labels[lbl["garbage_label_id"]] = lbl["garbage_label_title"]

        # parse items
        entries = []
        for item in cal_data.get("items", []):
            label_id = item["garbage_label_id"]
            # skip parent-only labels that have no actual schedule meaning
            if label_id not in labels:
                continue
            date_str = item["garbage_calendar_item_date"]  # "DD.MM.YYYY"
            date = datetime.strptime(date_str, "%d.%m.%Y").date()
            waste_type = labels[label_id]

            entries.append(Collection(date=date, t=waste_type))

        _LOGGER.debug(
            "Fetched %d collection entries for '%s' (calendar %s)",
            len(entries),
            self._street,
            calendar_id,
        )

        return entries
