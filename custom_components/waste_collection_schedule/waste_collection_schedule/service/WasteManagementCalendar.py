"""Waste Management guest calendar retrieval; no login is required."""

from __future__ import annotations

import datetime
import re
from typing import Any

from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_REST_BASE = "https://rest-api.wm.com/"
_TIMEOUT = 30
_MAX_RETRIES = 3
_BACKOFF_FACTOR = 2
_RETRY_STATUS_CODES = (502, 503, 504)
_API_KEY_GUEST = "498C9CEE262DA37A80AA"
_API_KEY_HOLIDAYS = "C2068E03CB6B73D4FEBA"
_HOLIDAY_DATE_RE = re.compile(
    "\\d{1,2}/\\d{1,2}(?:/(?:\\d{4}|\\d{2}))?|\\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2}(?:st|nd|rd|th)?(?:,\\s*\\d{4})?",
    re.IGNORECASE,
)
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
_DELAY_RE = re.compile(
    "(?:(?P<before>\\d+)(?: days?)? delay|delay(?: of| by)?(?: up to)?\\s+(?:(?P<after>\\d+)|(?P<word>"
    + "|".join(_NUMBER_WORDS)
    + "))\\b(?: days?)?)",
    re.IGNORECASE,
)
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Enter your WM service address. No account is needed — this uses the same guest lookup as wm.com/us/en/mywm/my-services/view-pickup-eta."
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


def _guest_headers(api_key: str) -> dict[str, str]:
    return {
        "accept": "application/json, text/plain, */*",
        "apiKey": api_key,
        "origin": "https://www.wm.com",
        "referer": "https://www.wm.com/",
    }


def _parse_holiday_message(
    message: str, today: datetime.date | None = None
) -> dict[datetime.datetime, datetime.datetime]:
    """
    Parse a WM holiday text message into a mapping of
    original_date -> adjusted_date.

    WM returns human-readable strings such as:
      "Due to the Thanksgiving holiday, your service on 11/24 will be on
       a 1 day delay."

    ``today`` is the reference date used to resolve messages that omit the
    year; it defaults to the current date and exists so tests can pin it.
    """
    if today is None:
        today = datetime.date.today()
    date_spans: list[tuple[datetime.datetime, int, int]] = []
    for m in _HOLIDAY_DATE_RE.finditer(message):
        raw = m.group()
        try:
            if "/" in raw:
                has_year = raw.count("/") == 2
                if has_year:
                    year_format = "%y" if len(raw.rsplit("/", 1)[1]) == 2 else "%Y"
                    dt = datetime.datetime.strptime(raw, f"%m/%d/{year_format}")
                else:
                    dt = datetime.datetime.strptime(raw, "%m/%d").replace(
                        year=today.year
                    )
            else:
                raw = re.sub("(\\d)(?:st|nd|rd|th)\\b", "\\1", raw)
                has_year = "," in raw
                date_format = "%B %d, %Y" if has_year else "%B %d"
                dt = datetime.datetime.strptime(raw, date_format)
                if not has_year:
                    dt = dt.replace(year=today.year)
            if not has_year and dt.date() + datetime.timedelta(days=6) < today:
                dt = dt.replace(year=today.year + 1)
        except ValueError:
            continue
        date_spans.append((dt, m.start(), m.end()))
    result: dict[datetime.datetime, datetime.datetime] = {}
    for i, (dt, _start, end) in enumerate(date_spans):
        next_start = date_spans[i + 1][1] if i + 1 < len(date_spans) else len(message)
        segment = message[end:next_start]
        delay_match = _DELAY_RE.search(segment)
        if not delay_match:
            continue
        digits = delay_match.group("before") or delay_match.group("after")
        if digits:
            offset = int(digits)
        else:
            offset = _NUMBER_WORDS.get((delay_match.group("word") or "").lower(), 1)
        if "weekday collections" in segment.lower():
            collection_date = dt
            if collection_date.weekday() == 5:
                collection_date -= datetime.timedelta(days=1)
            elif collection_date.weekday() == 6:
                collection_date += datetime.timedelta(days=1)
            while collection_date.weekday() < 5:
                result[collection_date] = collection_date + datetime.timedelta(
                    days=offset
                )
                collection_date += datetime.timedelta(days=1)
        else:
            result[dt] = dt + datetime.timedelta(days=offset)
    return result


class _CalendarClient:
    _session: Any

    def __init__(
        self, street: str, city: str, state: str, zip_code: str, country: str = "US"
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
                "No WM account found for this address. Check that the street, city, state, and ZIP are correct.",
            )
        accounts = resp.json().get("accounts") or []
        if not accounts:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No WM account found for this address. Check that the street, city, state, and ZIP are correct.",
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
        return resp.json().get("services") or []

    def _get_pickup_info(
        self, session: requests.Session, ezpay_id: str, service_id: str
    ) -> Any:
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
        return resp

    def _parse_pickup_info(self, resp):
        if resp.status_code == 204 or not resp.content:
            return []
        body = resp.json()
        results: list[tuple[str, str, datetime.date]] = []
        waste_streams: dict = (body.get("data") or {}).get("wasteStreams") or {}
        for stream_code, stream_data in waste_streams.items():
            for svc in stream_data.get("services") or []:
                name: str = (
                    svc.get("containerType") or stream_code.replace("_", " ").title()
                )
                pickup_dates: list[str] = (svc.get("pickupScheduleInfo") or {}).get(
                    "pickupDates"
                ) or []
                for date_str in pickup_dates:
                    try:
                        date = datetime.datetime.strptime(date_str, "%m-%d-%Y").date()
                    except ValueError:
                        continue
                    results.append((name, stream_code, date))
        return results

    def _get_holiday_adjustments(self, session: requests.Session) -> Any:
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
        return resp

    def _parse_holiday_adjustments(self, resp):
        if resp.status_code == 204 or not resp.content:
            return {}
        adjustments: dict[datetime.datetime, datetime.datetime] = {}
        for holiday in resp.json().get("holidayData") or []:
            msg = holiday.get("holidayHours") or ""
            if msg:
                adjustments.update(_parse_holiday_message(msg))
        return adjustments

    def retrieve(self) -> Any:
        session = self._session
        ezpay_id = self._search_account(session)
        services = self._get_services(session, ezpay_id)
        if not services:
            raise SourceArgumentNotFound(
                "street", self._street, "No active WM services found for this address."
            )
        responses = []
        for svc in services:
            service_id = str(svc["serviceId"])
            responses.append(self._get_pickup_info(session, ezpay_id, service_id))
        holidays = self._get_holiday_adjustments(session)
        return responses, holidays

    def parse(self, response):
        responses, holidays = response
        raw = [item for resp in responses for item in self._parse_pickup_info(resp)]
        if not raw:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                "No upcoming pickup dates found for this address.",
            )
        holiday_map = self._parse_holiday_adjustments(holidays)
        entries: list[dict] = []
        for name, stream_code, pickup_date in raw:
            final_date = pickup_date
            if holiday_map:
                as_dt = datetime.datetime(
                    pickup_date.year, pickup_date.month, pickup_date.day
                )
                if as_dt in holiday_map:
                    final_date = holiday_map[as_dt].date()
            entries.append({"date": final_date, "type": stream_code, "label": name})
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
