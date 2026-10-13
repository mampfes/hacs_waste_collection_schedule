"""RirCalendar retrieval and parsing, using the pipeline HTTP session."""

import json
import time
from datetime import date
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import RetrieverFunc

ADDRESS_SUGGESTION_URL = (
    "https://www.rir.no/actions/rir/location/get-address-suggestion"
)
PICKUP_DATES_URL = (
    "https://www.rir.no/actions/rir/content/get-pickup-dates-by-address-id"
)
MONTHS_AHEAD = 13
EMPTY_RESULT_RETRIES = 3
EMPTY_RESULT_RETRY_DELAY = 1.0
REQUEST_DELAY = 0.3


def _normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())


class _CalendarClient:
    _session: Any

    def __init__(self, address: str):
        self._address = address

    def _get_address_id(self, session: requests.Session) -> str:
        r = session.get(ADDRESS_SUGGESTION_URL, params={"query": self._address})
        r.raise_for_status()
        options = r.json().get("Options", [])
        address_norm = _normalize(self._address)
        for option in options:
            if _normalize(option["Text"]) == address_norm:
                return str(option["Id"])
        if len(options) == 1:
            return str(options[0]["Id"])
        raise SourceArgumentNotFoundWithSuggestions(
            "address", self._address, [option["Text"] for option in options]
        )

    def _get_month_wrappers(
        self, session: requests.Session, address_id: str, year: int, month: int
    ):
        if month == 12:
            last_day = 31
        else:
            last_day = (date(year, month + 1, 1) - date(year, month, 1)).days
        date_from = f"{year}-{month:02d}"
        date_to = f"{year}-{month:02d}-{last_day:02d}"
        date_param = json.dumps(
            {"title": date_from, "dateFrom": date_from, "date": date_to}
        )
        wrappers = []
        for attempt in range(EMPTY_RESULT_RETRIES + 1):
            r = session.get(
                PICKUP_DATES_URL, params={"date": date_param, "addressId": address_id}
            )
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            wrappers = soup.select(".collectionCalendar__date-wrapper")
            if wrappers or attempt == EMPTY_RESULT_RETRIES:
                break
            time.sleep(EMPTY_RESULT_RETRY_DELAY)
        return r

    def retrieve(self):
        session = self._session
        address_id = self._get_address_id(session)
        today = date.today()
        year, month = today.year, today.month
        responses = []
        for i in range(MONTHS_AHEAD):
            if i:
                time.sleep(REQUEST_DELAY)
            responses.append(self._get_month_wrappers(session, address_id, year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1
        return responses


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()
