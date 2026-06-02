"""Source for Waste Management (wm.com) residential pickup schedules.

Uses the unauthenticated guest lookup flow from the MyWM pickup ETA page.
No account or credentials required — only a service address.

Guest API flow:
  1. GET rest-api.wm.com/account/search  (address → hashed ezpayId token)
  2. GET rest-api.wm.com/account/{ezpayId}/services  (list waste stream services)
  3. GET rest-api.wm.com/account/{ezpayId}/services/{serviceId}/pickupinfo  (dates)
  4. GET rest-api.wm.com/holidays  (holiday shift adjustments)

All four calls use a single guest API key with no authentication headers.
The API keys are embedded in WM's JavaScript bundle and may be rotated; if
requests start returning 401 errors, open an issue so they can be updated.
"""

from __future__ import annotations

import datetime
import re

import requests

from ..collection import Collection
from ..exceptions import SourceArgumentNotFound
from ..icons import Icons

# ---------------------------------------------------------------------------
# Module-level metadata
# ---------------------------------------------------------------------------

TITLE = "Waste Management (WM)"
DESCRIPTION = (
    "Source for Waste Management (wm.com) residential pickup schedules "
    "using the guest address lookup — no account required."
)
URL = "https://www.wm.com"
COUNTRY = "us"

TEST_CASES: dict[str, dict] = {
    "Example Address": {
        "street": "245 Emerson Ave",
        "city": "Ypsilanti",
        "state": "MI",
        "zip_code": "48198",
    },
}

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REST_BASE = "https://rest-api.wm.com/"
_TIMEOUT = 30

# Guest API keys embedded in WM's JavaScript bundle, one per endpoint group.
_API_KEY_GUEST = "498C9CEE262DA37A80AA"  # account search, services, pickupinfo
_API_KEY_HOLIDAYS = "C2068E03CB6B73D4FEBA"  # holidays endpoint

# Regexes for parsing holiday delay messages, e.g.:
#   "Due to the Thanksgiving holiday, service on 11/24 will be on a 1 day delay."
_HOLIDAY_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?")
_DELAY_RE = re.compile(r"(\d+)(?: day)? delay", re.IGNORECASE)

# WM wasteStreamGroupCode values → canonical Icons enum
ICON_MAP: dict[str, Icons] = {
    "GARBAGE": Icons.GENERAL_WASTE,
    "RECYCLABLE": Icons.RECYCLING,
    "YARD_WASTE": Icons.GARDEN,
    "ORGANIC": Icons.ORGANIC,
    "BULK": Icons.BULKY,
    "HAZARDOUS": Icons.HAZARDOUS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your WM service address. No account is needed — this uses "
        "the same guest lookup as wm.com/us/en/mywm/my-services/view-pickup-eta."
    )
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street": "Street address (e.g. '123 Main St')",
        "city": "City name",
        "state": "Two-letter state code (e.g. 'MI')",
        "zip_code": "5-digit ZIP code",
        "country": "Country code — 'US' or 'CA' (default: US)",
    }
}

PARAM_TRANSLATIONS = {
    "en": {
        "street": "Street Address",
        "city": "City",
        "state": "State",
        "zip_code": "ZIP Code",
        "country": "Country",
    }
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _guest_headers(api_key: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "apiKey": api_key,
        "origin": "https://www.wm.com",
        "referer": "https://www.wm.com/",
    }


def _parse_holiday_message(
    message: str,
) -> dict[datetime.datetime, datetime.datetime]:
    """
    Parse a WM holiday text message into a mapping of
    original_date -> adjusted_date.

    WM returns human-readable strings such as:
      "Due to the Thanksgiving holiday, your service on 11/24 will be on
       a 1 day delay."
    """
    today = datetime.datetime.today()
    date_spans: list[tuple[datetime.datetime, int, int]] = []

    for m in _HOLIDAY_DATE_RE.finditer(message):
        raw = m.group()
        try:
            if raw.count("/") == 2:
                dt = datetime.datetime.strptime(raw, "%m/%d/%Y")
            else:
                dt = datetime.datetime.strptime(raw, "%m/%d").replace(year=today.year)
                if dt < today:
                    dt = dt.replace(year=today.year + 1)
        except ValueError:
            continue
        date_spans.append((dt, m.start(), m.end()))

    result: dict[datetime.datetime, datetime.datetime] = {}
    for i, (dt, _start, end) in enumerate(date_spans):
        next_start = date_spans[i + 1][1] if i + 1 < len(date_spans) else len(message)
        segment = message[end:next_start]
        delay_match = _DELAY_RE.search(segment)
        offset = int(delay_match.group(1)) if delay_match else 0
        result[dt] = dt + datetime.timedelta(days=offset)

    return result


# ---------------------------------------------------------------------------
# Source class
# ---------------------------------------------------------------------------


class Source:
    def __init__(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str,
        country: str = "US",
    ) -> None:
        self._street = street
        self._city = city
        self._state = state
        self._zip_code = zip_code
        self._country = country.upper()

    def _search_account(self, session: requests.Session) -> str:
        """
        Step 1: Resolve the service address to a hashed ezpayId token.
        Returns the ezpayId string used in all subsequent API calls.
        """
        resp = session.get(
            _REST_BASE + "account/search",
            params={
                "street": self._street,
                "city": self._city,
                "state": self._state,
                "country": self._country,
                "address": f"{self._street}, {self._city}, {self._state}",
                "postalCode": self._zip_code,
                "lang": "en_US",
            },
            headers=_guest_headers(_API_KEY_GUEST),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No WM account found for this address. "
                "Check that the street, city, state, and ZIP are correct.",
            )

        accounts = resp.json().get("accounts") or []
        if not accounts:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No WM account found for this address. "
                "Check that the street, city, state, and ZIP are correct.",
            )

        return accounts[0]["ezpayId"]

    def _get_services(self, session: requests.Session, ezpay_id: str) -> list[dict]:
        """
        Step 2: List the waste collection services on this account.
        Returns a list of service dicts with at least 'serviceId' and
        'serviceDescription'.
        """
        resp = session.get(
            _REST_BASE + f"account/{ezpay_id}/services",
            params={"lang": "en_US", "serviceChangeEligibility": "Y"},
            headers=_guest_headers(_API_KEY_GUEST),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return []

        return resp.json().get("services", [])

    def _get_pickup_info(
        self,
        session: requests.Session,
        ezpay_id: str,
        service_id: str,
    ) -> list[tuple[str, str, datetime.date]]:
        """
        Step 3: Fetch pickup dates for one service.
        Returns a list of (waste_type_name, waste_stream_code, date) tuples.
        """
        resp = session.get(
            _REST_BASE + f"account/{ezpay_id}/services/{service_id}/pickupinfo",
            params={"lang": "en_US", "checkAlerts": "Y"},
            headers=_guest_headers(_API_KEY_GUEST),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return []

        body = resp.json()
        results: list[tuple[str, str, datetime.date]] = []

        waste_streams: dict = body.get("data", {}).get("wasteStreams", {})
        for stream_code, stream_data in waste_streams.items():
            for svc in stream_data.get("services", []):
                # Use containerType for the human-readable name if available,
                # falling back to the stream code itself.
                name: str = (
                    svc.get("containerType") or stream_code.replace("_", " ").title()
                )
                pickup_dates: list[str] = svc.get("pickupScheduleInfo", {}).get(
                    "pickupDates", []
                )
                for date_str in pickup_dates:
                    try:
                        date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()
                    except ValueError:
                        continue
                    results.append((name, stream_code, date))

        return results

    def _get_holiday_adjustments(
        self, session: requests.Session
    ) -> dict[datetime.datetime, datetime.datetime]:
        """
        Step 4: Fetch upcoming holiday schedule shifts for this address.
        """
        resp = session.get(
            _REST_BASE + "holidays",
            params={
                "lang": "en_US",
                "street": self._street,
                "city": self._city,
                "state": self._state,
                "postalCode": self._zip_code,
                "country": self._country,
                "type": "upcoming",
            },
            headers=_guest_headers(_API_KEY_HOLIDAYS),
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()

        if resp.status_code == 204 or not resp.content:
            return {}

        adjustments: dict[datetime.datetime, datetime.datetime] = {}
        for holiday in resp.json().get("holidayData", []):
            msg = holiday.get("holidayHours", "")
            if msg:
                adjustments.update(_parse_holiday_message(msg))
        return adjustments

    # ------------------------------------------------------------------
    # Public fetch
    # ------------------------------------------------------------------

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1 – resolve address to hashed account token.
        ezpay_id = self._search_account(session)

        # Step 2 – list services on this account.
        services = self._get_services(session, ezpay_id)
        if not services:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No active WM services found for this address.",
            )

        # Step 3 – get pickup dates per service.
        raw: list[tuple[str, str, datetime.date]] = []
        for svc in services:
            service_id = str(svc["serviceId"])
            raw.extend(self._get_pickup_info(session, ezpay_id, service_id))

        if not raw:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No upcoming pickup dates found for this address.",
            )

        # Step 4 – fetch holiday adjustments.
        holiday_map = self._get_holiday_adjustments(session)

        entries: list[Collection] = []
        for name, stream_code, pickup_date in raw:
            final_date = pickup_date
            if holiday_map:
                as_dt = datetime.datetime(
                    pickup_date.year, pickup_date.month, pickup_date.day
                )
                if as_dt in holiday_map:
                    final_date = holiday_map[as_dt].date()

            entries.append(
                Collection(
                    date=final_date,
                    t=name,
                    icon=ICON_MAP.get(stream_code, Icons.GENERAL_WASTE),
                )
            )

        return entries
