"""NorthumberlandCalendar retrieval and parsing, using the pipeline HTTP session."""

import logging
import re
from datetime import date, datetime
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

_LOGGER = logging.getLogger(__name__)
BASE_URL = "https://bincollection.northumberland.gov.uk"


def _parse_date(text: str):
    text = re.sub(
        "^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = text.strip()
    today = date.today()
    for fmt in ("%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    for fmt in ("%d %B", "%d %b"):
        try:
            d = datetime.strptime(f"{text} 2000", f"{fmt} %Y")
            candidate = d.replace(year=today.year).date()
            if candidate >= today:
                return candidate
            return d.replace(year=today.year + 1).date()
        except ValueError:
            continue
    return None


class _CalendarClient:
    _session: Any

    def __init__(self, uprn: str | int, postcode: str):
        self._uprn = str(uprn)
        self._postcode = postcode.strip()

    def retrieve(self) -> Any:
        session = self._session
        r1 = session.get(f"{BASE_URL}/postcode")
        r1.raise_for_status()
        soup1 = BeautifulSoup(r1.text, "html.parser")
        csrf_input = soup1.find("input", {"name": "_csrf"})
        if csrf_input is None:
            raise ValueError(
                "Could not find CSRF token on the postcode page. The site may have changed."
            )
        csrf_token1 = csrf_input.get("value", "")
        r2 = session.post(
            f"{BASE_URL}/postcode",
            data={"_csrf": csrf_token1, "postcode": self._postcode},
            allow_redirects=True,
        )
        r2.raise_for_status()
        soup2 = BeautifulSoup(r2.text, "html.parser")
        csrf_input2 = soup2.find("input", {"name": "_csrf"})
        if csrf_input2 is None:
            raise ValueError(
                "Could not find CSRF token on the address-select page. The site may have changed."
            )
        csrf_token2 = csrf_input2.get("value", "")
        r3 = session.post(
            f"{BASE_URL}/address-select",
            data={"_csrf": csrf_token2, "address": self._uprn},
            allow_redirects=True,
        )
        r3.raise_for_status()
        return r3

    def parse(self, response):
        return self._parse_schedule(response.text)

    def _parse_schedule(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        entries = []
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            date_text = cells[0].get_text(strip=True)
            if date_text.lower() == "date":
                continue
            bin_type = cells[2].get_text(strip=True)
            if not bin_type:
                continue
            d = _parse_date(date_text)
            if d is None:
                _LOGGER.warning(
                    "Could not parse date %r for bin type %r", date_text, bin_type
                )
                continue
            entries.append({"date": d, "type": bin_type})
        if entries:
            return entries
        bin_cals = soup.find_all("div", class_=re.compile("ncc-bin-calendar"))
        for bc in bin_cals:
            paras = bc.find_all("p")
            if len(paras) < 3:
                continue
            bin_type = paras[0].get_text(strip=True)
            date_text = paras[2].get_text(strip=True)
            if not bin_type:
                continue
            d = _parse_date(date_text)
            if d is None:
                _LOGGER.warning(
                    "Could not parse date %r for bin type %r", date_text, bin_type
                )
                continue
            entries.append({"date": d, "type": bin_type})
        if entries:
            return entries
        dts = soup.find_all("dt")
        for dt in dts:
            bin_type = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")
            if dd is None:
                continue
            date_text = dd.get_text(strip=True)
            d = _parse_date(date_text)
            if d is None:
                continue
            entries.append({"date": d, "type": bin_type})
        if not entries:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data found. Please check your UPRN and postcode are correct.",
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
