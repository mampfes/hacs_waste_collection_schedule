"""SouthamptonCalendar retrieval and parsing, using the pipeline HTTP session."""

import logging
import re
import time
from datetime import datetime
from typing import Any

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

REGEX = "(Food|Glass|Recycling|General Waste|Garden Waste).*?([0-9]{1,2}\\/[0-9]{1,2}\\/[0-9]{4})"
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 3
_LOGGER = logging.getLogger(__name__)


class _CalendarClient:
    _session: Any

    def __init__(self, uprn):
        self._uprn = str(uprn)

    def retrieve(self):
        url = f"https://www.southampton.gov.uk/whereilive/waste-calendar?UPRN={self._uprn}"
        calendar_view_only = None
        last_status = None
        for attempt in range(1, MAX_RETRIES + 1):
            s = self._session
            r = s.get(url)
            last_status = r.status_code
            if r.ok:
                match = re.search("#calendar1.*?listView", r.text, flags=re.DOTALL)
                if match:
                    calendar_view_only = match[0]
                    break
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
        if calendar_view_only is None:
            raise ValueError(
                f"Unable to retrieve the waste calendar from southampton.gov.uk after {MAX_RETRIES} attempts (last HTTP status: {last_status}). This is usually caused by the council's anti-bot protection (Incapsula) blocking the request; please try again later."
            )
        return r

    def parse(self, response):
        match = re.search(r"#calendar1.*?listView", response.text, flags=re.DOTALL)
        if match is None:
            raise ValueError("The response contains no Southampton waste calendar")
        calendar_view_only = match[0]
        results = re.findall(REGEX, calendar_view_only)
        entries = []
        for item in results:
            entries.append(
                {"date": datetime.strptime(item[1], "%m/%d/%Y").date(), "type": item[0]}
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
