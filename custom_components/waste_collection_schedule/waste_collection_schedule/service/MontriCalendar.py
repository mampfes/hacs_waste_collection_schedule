"""MontriCalendar retrieval and parsing through the shared, verified HTTP session."""

import unicodedata
import uuid
from datetime import date, datetime
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_BASE = "https://frontend.montri.fr"
TIMEZONE = ZoneInfo("Europe/Paris")
MONTHS_AHEAD = 6


def _normalize(value: str) -> str:
    """Lowercase and strip accents for fuzzy comparisons."""
    normalized = unicodedata.normalize("NFKD", value)
    return (
        "".join(c for c in normalized if not unicodedata.combining(c)).lower().strip()
    )


def _parse_local_date(iso_datetime: str) -> date:
    dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    return dt.astimezone(TIMEZONE).date()


class _CalendarClient:
    _session: Any

    def __init__(self, postal_code: str, city_name: str, address: str):
        self._postal_code = postal_code.strip()
        self._city_name = city_name.strip()
        self._address = address.strip()

    def _sign_in_anonymously(
        self,
        session: requests.Session,
        contract_id: str,
        city_insee_code: str,
        address_id: str,
    ) -> str:
        body = {
            "addressId": address_id,
            "cityInseeCode": city_insee_code,
            "contractId": contract_id,
            "isCguAccepted": False,
            "notificationGenerals": False,
            "notificationNews": False,
            "notificationPerturbations": False,
            "notificationRecyclingCenter": False,
            "notificationToken": "",
            "selectedRecyclingCenterId": "",
            "sorterLevel": "debutant",
            "userId": str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{API_BASE}:{contract_id}:{city_insee_code}:{address_id}",
                )
            ),
            "userType": "PRIVATE",
        }
        r = session.post(f"{API_BASE}/v1/auth/signInAnonymously", json=body, timeout=60)
        r.raise_for_status()
        return str(r.json()["currentAccessToken"])

    def _fetch_month(
        self, session: requests.Session, month: int, year: int
    ) -> requests.Response:
        return session.get(
            f"{API_BASE}/v1/calendar/tablemonth/fixed/{month}/{year}", timeout=100
        )

    def retrieve(self) -> Any:
        session = self._session
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        r = session.get(f"{API_BASE}/v1/city/find/{self._postal_code}", timeout=100)
        r.raise_for_status()
        cities = r.json()
        city = None
        city_names = []
        for c in cities:
            city_names.append(c["cityName"])
            if _normalize(c["cityName"]) == _normalize(self._city_name):
                city = c
                break
        if city is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "city_name", self._city_name, sorted(set(city_names))
            )
        token = self._sign_in_anonymously(
            session, city["contractId"], city["inseeCode"], ""
        )
        session.headers["Authorization"] = f"Bearer {token}"
        address = quote(self._address, safe="")
        r = session.get(
            f"{API_BASE}/v1/address/search/bycontract/{address}", timeout=100
        )
        r.raise_for_status()
        candidates = r.json()
        matches = [
            candidate
            for candidate in candidates
            if candidate.get("citycode") == city["inseeCode"]
        ]
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "address", self._address, [c["label"] for c in candidates]
            )
        today = date.today()
        first_table = None
        for candidate in matches:
            token = self._sign_in_anonymously(
                session, city["contractId"], city["inseeCode"], candidate["id"]
            )
            session.headers["Authorization"] = f"Bearer {token}"
            r = self._fetch_month(session, today.month, today.year)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            first_table = r.json()
            break
        if first_table is None:
            raise SourceArgumentException(
                "address",
                f"No collection calendar is available for {self._address!r} in {city['cityName']}. Try a neighbouring house number.",
            )
        r = session.get(f"{API_BASE}/v1/contract/trashflows", timeout=100)
        r.raise_for_status()
        flow_names = {
            flow["code"]: flow["name"] for flow in r.json() if flow.get("type") == "pap"
        }
        tables = [first_table]
        month, year = today.month, today.year
        for _ in range(1, MONTHS_AHEAD):
            month += 1
            if month > 12:
                month, year = 1, year + 1
            r = self._fetch_month(session, month, year)
            r.raise_for_status()
            tables.append(r.json())
        return tables, flow_names

    def parse(self, raw):
        tables, flow_names = raw
        entries = []
        for table in tables:
            for week in table.get("weeks", []):
                for day in week.values():
                    iso_date = day.get("date")
                    if not iso_date:
                        continue
                    collection_date = _parse_local_date(iso_date)
                    for code in day.get("data", []):
                        entries.append(
                            {
                                "date": collection_date,
                                "type": flow_names.get(code, code),
                            }
                        )
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
