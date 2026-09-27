"""LocalGov Drupal's Waste Collection module (UK councils).

`localgov_waste_collection <https://www.drupal.org/project/localgov_waste_collection>`_
is the bin-day lookup of the LocalGov Drupal distribution many UK councils run
their site on. Under a base path of the council's choosing it serves:

    {base}/find?postcode=...   an address picker (<select name="uprn">)
    {base}/view/{uprn}         the property's schedule

The schedule lists one ``.waste-collection__day`` element per round and date::

    <li class="waste-collection__day">
      <span class="waste-collection__day--day"><time datetime="04-09-2026">04</time></span>
      <span class="waste-collection__day--type">Grey recycling</span>
      <span class="waste-collection__day--colour ...">Grey</span>
    </li>

The ``datetime`` attribute is ISO on some sites and ``DD-MM-YYYY`` on others,
so :class:`CollectionDaysParser` reads both and yields ``(date, type)`` rows for
a ``RowTransformer``. Some councils name every round collected on a date in one
sentence ("Recycling, garden waste and food waste collections"); pass
``split=True`` for those.
"""

import datetime
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import (
    HttpGetRetriever,
    Lookup,
    LookupChainRetriever,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_TRAILING_COLLECTIONS = re.compile(r"\s+collections?\s*$", re.IGNORECASE)


def uprn_retriever(
    base: str, uprn: str = "uprn", *, normalise: "Callable[[str], str] | None" = None
) -> HttpGetRetriever:
    """The schedule of the property given by the ``uprn`` param."""

    def _url(**params: Any) -> str:
        value = str(params[uprn]).strip()
        return f"{base}/view/{normalise(value) if normalise else value}"

    return HttpGetRetriever(url=_url)


def address_retriever(
    base: str, postcode: str = "postcode", address: str = "address"
) -> LookupChainRetriever:
    """The schedule of the property whose address starts with the ``address``
    param, picked from the addresses the ``postcode`` param lists."""

    def _pick(response: Any, **params: Any) -> str:
        select = BeautifulSoup(response.text, "html.parser").select_one(
            'select[name="uprn"]'
        )
        # The picker is left out altogether for a postcode the site does not know.
        if select is None:
            raise SourceArgumentNotFound(postcode, params[postcode])
        options = [
            (str(option.get("value")), option.get_text(" ", strip=True))
            for option in select.select("option")
            if option.get("value")
        ]
        wanted = str(params[address]).strip().casefold()
        for value, text in options:
            if text.casefold().startswith(wanted):
                return value
        raise SourceArgumentNotFoundWithSuggestions(
            address, params[address], [text for _value, text in options]
        )

    return LookupChainRetriever(
        steps=(
            Lookup(
                f"{base}/find",
                params=lambda **params: {"postcode": str(params[postcode]).strip()},
                pick=_pick,
            ),
        ),
        url=lambda found_uprn, **_: f"{base}/view/{found_uprn}",
        raise_for_status=True,
    )


def _date(value: str) -> "datetime.date | None":
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _split(text: str) -> "list[str]":
    """ "Recycling, garden waste and food waste collections" -> its rounds."""
    text = _TRAILING_COLLECTIONS.sub("", text.strip()).replace(" and ", ", ")
    return [part.strip() for part in text.split(",") if part.strip()]


class CollectionDaysParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, type)`` rows from a schedule page's ``.waste-collection__day``s.

    Args:
        split: read the type as a sentence naming several rounds, one row
            each. A round named twice for one date (a separate garden-waste
            row beside a combined one) is emitted once.
    """

    def __init__(self, *, split: bool = False):
        self.split = split

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows: list[tuple[datetime.date, str]] = []
        seen: set[tuple[datetime.date, str]] = set()
        for day in soup.select(".waste-collection__day"):
            time = day.select_one("time[datetime]")
            label = day.select_one(".waste-collection__day--type")
            if time is None or label is None:
                continue
            date = _date(str(time["datetime"]))
            if date is None:
                continue
            text = label.get_text(" ", strip=True)
            for name in _split(text) if self.split else [text]:
                key = (date, name.casefold())
                if key not in seen:
                    seen.add(key)
                    rows.append((date, name))
        return rows
