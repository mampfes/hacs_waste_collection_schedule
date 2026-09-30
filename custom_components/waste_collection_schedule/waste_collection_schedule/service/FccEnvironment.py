"""FCC Environment council collection pages (Harborough, West Devon, South Hams).

FCC Environment runs the "your bin collections" page for several UK councils,
in two dialects keyed by a UPRN:

* ``detail-address`` (Harborough): one form POST of ``Uprn``, answered with a
  page whose "next scheduled bin collection days" block lists one ``li`` per
  service, the date in ``span.pull-right``.
* ``getcollectiondetails`` (West Devon, South Hams): the home page hands out an
  ``fcc_session_cookie`` that is posted back as ``fcc_session_token`` with the
  UPRN, answered with JSON whose ``binCollections.tile`` holds one HTML tile per
  service (an ``h3`` naming it, and a bold "next scheduled collection" date such
  as ``tomorrow, Thursday, 01 October 2026``).

The hosts send their leaf certificate without the intermediate, so no default
trust store can build a chain to it; the requests are made with
``verify=False``, as the legacy source did.

:class:`FccEnvironmentRetriever` issues the region's request and
:class:`FccEnvironmentParser` reads either reply into ``(date, label)`` rows.
Adding a council is an entry in ``SERVICES``.
"""

import datetime
import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, NamedTuple

from bs4 import BeautifulSoup

from waste_collection_schedule import date_parsers
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


class FccService(NamedTuple):
    """One council's endpoint."""

    endpoint: str
    #: The ``getcollectiondetails`` dialect posts back a token from this page.
    home: str | None = None


SERVICES: dict[str, FccService] = {
    "harborough": FccService("https://harborough.fccenvironment.co.uk/detail-address"),
    "westdevon": FccService(
        "https://westdevon.fccenvironment.co.uk/ajaxprocessor/getcollectiondetails",
        home="https://westdevon.fccenvironment.co.uk/",
    ),
    "southhams": FccService(
        "https://waste.southhams.gov.uk/mycollections/getcollectiondetails",
        home="https://waste.southhams.gov.uk/",
    ),
}

_TOKEN = re.compile(r"fcc_session_cookie=([^;,\s]+)")
_DATE = re.compile(r"\d{1,2} [A-Za-z]+ \d{4}")
_PARSE_DATE = date_parsers.for_format("%d %B %Y")


class FccEnvironmentRetriever:
    """The region's collection reply for ``source.params['uprn']``."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> Any:
        region = str(source.params.get("region", "harborough"))
        service = SERVICES.get(region)
        if service is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "region", region, list(SERVICES)
            )
        uprn = source.params["uprn"]
        session = source.session
        if service.home is None:
            response = session.post(
                service.endpoint,
                data={"Uprn": uprn},
                verify=False,
                timeout=self.timeout,
            )
        else:
            home = session.get(service.home, verify=False, timeout=self.timeout)
            home.raise_for_status()
            # Read off the Set-Cookie header (not a cookie jar) so the token is
            # the one this very reply carried.
            match = _TOKEN.search(home.headers.get("set-cookie") or "")
            if match is None:
                raise ValueError("FCC Environment sent no session token")
            token = match.group(1)
            response = session.post(
                service.endpoint,
                data={"fcc_session_token": token, "uprn": uprn},
                headers={"x-requested-with": "XMLHttpRequest"},
                verify=False,
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response


class FccEnvironmentParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, label)`` rows, one per service, from either dialect's reply.

    ``labels`` are the wordings worth keeping (``"refuse"``, ``"recycling"``);
    a service names one of them in its heading, and the row carries that
    wording rather than the whole heading. A service naming none of them is
    skipped, as is one with no date (Harborough's garden waste line carries a
    subscription notice instead). The JSON dialect repeats each service once
    per container image; identical rows are kept once.
    """

    def __init__(self, labels: Iterable[str]):
        self.labels = tuple(label.lower() for label in labels)

    def _label(self, heading: str) -> str | None:
        lowered = heading.lower()
        return next((label for label in self.labels if label in lowered), None)

    def _rows(self, headings_dates: Iterable[tuple[str, str]]):
        seen: set[tuple[datetime.date, str]] = set()
        rows: list[tuple[datetime.date, str]] = []
        for heading, text in headings_dates:
            label = self._label(heading)
            match = _DATE.search(text)
            if label is None or match is None:
                continue
            try:
                row = (_PARSE_DATE(match.group(0)), label)
            except ValueError:
                continue
            if row not in seen:
                seen.add(row)
                rows.append(row)
        return rows

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        if response.text.lstrip().startswith("{"):
            tiles = (response.json().get("binCollections") or {}).get("tile") or []
            found = []
            for tile in tiles:
                soup = BeautifulSoup(tile[0], "html.parser")
                heading = soup.find("h3")
                bold = soup.find_all("b")
                # The last bold element is the next date ("tomorrow, Thursday,
                # 01 October 2026"); the weekday alone is not a date.
                if heading is not None and bold:
                    found.append((heading.get_text(), bold[-1].get_text()))
            return self._rows(found)
        soup = BeautifulSoup(response.text, "html.parser")
        found = []
        for item in soup.select("div.block-your-next-scheduled-bin-collection-days li"):
            span = item.select_one("span.pull-right")
            if span is not None:
                span.extract()
                found.append((item.get_text(), span.get_text(strip=True)))
        return self._rows(found)
