"""Drupal "find your bin collection day" forms with holiday adjustments (UK).

Wokingham's page is a three-step Drupal form (``waste_collection_api_form``) that
posts back to its own address and carries a ``form_build_id`` token from one
step to the next::

    GET  {page}                    the form and its token, plus the council's
                                   table of holiday adjustments
    POST {page}                    postcode_search + op=Find Address
                                   -> the address picker (``address_options``)
    POST {page}                    postcode_search + address_options
                                   + op=Show collection dates
                                   -> one ``.card--waste`` card per round

A card names the round in its ``<h3>`` (sometimes suffixed "(week 1)") and the
next date in its first ``<span>`` ("Tuesday 06/10/2026", or "No collection").

Around public holidays the council publishes a table of ``normal date -> new
date`` rows with no year ("Thursday 25 December" -> "Friday 26 December"). The
cards still show the normal date, so :class:`WasteCardsParser` moves each date
the table lists. The table is part of the page, so it is read from every
response :class:`WasteFormRetriever` hands over, the first page taking
precedence.
"""

import datetime
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_DAY_MONTH = re.compile(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)")
_NAME = "Drupal waste form"

# (day, month) of a normal collection date -> (day, month) it is moved to
Revisions = dict[tuple[int, int], tuple[int, int]]


def _build_id(response: Any) -> str:
    field = BeautifulSoup(response.text, "html.parser").find(
        "input", {"name": "form_build_id"}
    )
    value = field.get("value") if field is not None else None
    if not isinstance(value, str):
        response_shape.expect(
            False,
            source_name=_NAME,
            detail="bin collection page carries no form_build_id",
            raw=response.text,
        )
    return str(value)


class WasteFormRetriever:
    """The collection cards of the property the params name.

    Returns ``[form page, results page]``: the first page for its holiday
    adjustments, the last for the cards. The property is the ``property`` param
    when given, otherwise the first address of the ``postcode`` param's picker
    that contains the ``address`` param (commas ignored, case folded).

    Args:
        page: the form's URL.
        form_id: the Drupal ``form_id`` the form posts back.
        postcode: name of the param holding the postcode.
        property: name of the param holding the picker's option value.
        address: name of the param holding (part of) the address text.
    """

    def __init__(
        self,
        page: str,
        *,
        form_id: str = "waste_collection_api_form",
        postcode: str = "postcode",
        property: str = "property",
        address: str = "address",
    ):
        self.form_id = form_id
        self.postcode = postcode
        self.property = property
        self.address = address
        parts = urlsplit(page)
        headers = {"Origin": f"{parts.scheme}://{parts.netloc}", "Referer": page}
        self._page = Request(page)
        self._find = Request(
            page,
            method="POST",
            headers=headers,
            data=lambda build_id, **params: {
                "postcode_search": self._postcode(params),
                "op": "Find Address",
                "form_build_id": build_id,
                "form_id": form_id,
            },
        )
        self._show = Request(
            page,
            method="POST",
            headers=headers,
            data=lambda build_id, chosen, **params: {
                "postcode_search": self._postcode(params),
                "address_options": chosen,
                "op": "Show collection dates",
                "form_build_id": build_id,
                "form_id": form_id,
            },
        )

    def _postcode(self, params: Any) -> str:
        return str(params[self.postcode]).upper().strip().replace(" ", "")

    def _property(self, response: Any, params: Any) -> str:
        """The picker option for the params: the given property, else by address."""
        options = [
            (str(option.get("value")), option.get_text(" ", strip=True))
            for option in BeautifulSoup(response.text, "html.parser").select(
                "div.form-item__dropdown option"
            )
            if option.get("value")
        ]
        if params.get(self.property) is not None:
            return str(params[self.property])
        if not options:
            raise SourceArgumentNotFound(self.postcode, params[self.postcode])
        wanted = str(params[self.address]).replace(",", "").strip().casefold()
        for value, text in options:
            if wanted in text.replace(",", "").casefold():
                return value
        raise SourceArgumentNotFoundWithSuggestions(
            self.address, params[self.address], [text for _value, text in options]
        )

    def __call__(self, source: "BaseSource") -> list[Any]:
        page = self._page(source)
        found = self._find(source, _build_id(page))
        chosen = self._property(found, source.params)
        results = self._show(source, _build_id(found), chosen)
        return [page, results]


def _day_month(text: str) -> tuple[int, int] | None:
    """ "Thursday 25 December" -> (25, 12); None when it is not a dated weekday."""
    match = _DAY_MONTH.search(text)
    if not match:
        return None
    weekday = recurrence.weekday(match.group(1))
    month = recurrence.month(match.group(3))
    if weekday is None or month is None:
        return None
    return int(match.group(2)), month


def _revisions(html: str) -> Revisions:
    """The rescheduled dates of the page's adjustments table; "No change" rows
    and rows that do not read as two dates are ignored."""
    revised: Revisions = {}
    for row in BeautifulSoup(html, "html.parser").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        normal = _day_month(cells[0].get_text(" ", strip=True))
        new = _day_month(cells[1].get_text(" ", strip=True))
        if normal is None or new is None or normal == new:
            continue
        revised[normal] = new
    return revised


def _apply(revised: Revisions, date: datetime.date) -> datetime.date:
    new = revised.get((date.day, date.month))
    if new is None:
        return date
    day, month = new
    year = date.year + (1 if month < date.month else 0)
    try:
        return date.replace(year=year, month=month, day=day)
    except ValueError:
        return date


class WasteCardsParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, round)`` rows from the results page's ``.card--waste`` cards,
    moved to the rescheduled date wherever the adjustments table lists one."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        pages: Sequence[Any] = (
            response if isinstance(response, (list, tuple)) else [response]
        )
        revised: Revisions = {}
        for page in pages:
            for key, value in _revisions(page.text).items():
                revised.setdefault(key, value)

        rows: list[tuple[datetime.date, str]] = []
        soup = BeautifulSoup(pages[-1].text, "html.parser")
        for card in soup.find_all("div", {"class": "card--waste"}):
            heading = card.find("h3")
            span = card.find("span")
            if heading is None or span is None:
                continue
            words = span.get_text().strip().split()
            try:
                date = datetime.datetime.strptime(words[-1], "%d/%m/%Y").date()
            except (ValueError, IndexError):
                # "No collection": the round has no date yet
                continue
            # a round may be suffixed "(week 1)" or "(week 2)"
            rows.append(
                (_apply(revised, date), heading.get_text().split("(")[0].strip())
            )
        return rows
