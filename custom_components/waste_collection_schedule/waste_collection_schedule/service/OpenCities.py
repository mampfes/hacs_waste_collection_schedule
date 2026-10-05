"""OpenCities / MyArea widget platform (BaseSource architecture).

Many AU/NZ council websites expose the same two endpoints on their own domain
(the widget behind e.g. https://www.logan.qld.gov.au/MyLogan):

- ``GET <domain>/api/v1/myarea/search[fuzzy]``: address search, returning JSON
  ``{"Items": [{"Id": "<geolocation-guid>", "AddressSingleLine": ...}]}`` (a
  handful of legacy deployments answer with XML instead).
- ``GET <domain>/ocapi/Public/myarea/wasteservices``: given a ``geolocationid``,
  returns ``{"success": bool, "responseContent": "<html>"}`` where the HTML is
  a series of ``<article>`` / ``div.waste-services-result`` blocks, each with an
  ``<h3>`` (waste type), a ``.next-service`` element (the next collection date)
  and usually a ``.note`` element (the service's cadence and kerbside
  instructions in prose).

The platform is split the way the pipeline wants it:

``OpenCitiesRetriever``
    HTTP only: the optional warm-up page, the address search and the
    ``wasteservices`` call. Resolves an address to a geolocation id (or takes
    the id directly from a param) and returns the raw reply. The id is cached
    per source, so a source that is polled repeatedly pays for the search once.
``OpenCitiesParser``
    No I/O. Reads the ``wasteservices`` HTML into ``{"type", "date", "note"}``
    records (one per service that states a date), for a ``JsonTransformer``.
``OpenCitiesProjection``
    Optional preprocessor. The API returns only the *next* date per service, so
    where the note states the cadence ("Collected fortnightly") this projects
    the following dates as well.

A council is therefore a domain plus whatever quirks its deployment has (a
``pageLink``, a warm-up page, a differently formatted date), and its
``type_value_map``.
"""

from __future__ import annotations

import datetime
import logging
import re
from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING, Any, Literal, NamedTuple
from weakref import WeakKeyDictionary, WeakSet

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule import recurrence, response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Preprocessor
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_LOGGER = logging.getLogger(__name__)

DEFAULT_DATE_FORMAT = "%a %d/%m/%Y"

_WASTESERVICES_PATH = "/ocapi/Public/myarea/wasteservices"

# Bin labels that recur across the councils on this platform but that the shared
# vocabulary cannot resolve on its own ("Landfill" is a council's word for its
# general waste bin, "Organics" for its food-and-garden bin). Mapped once here
# so each council's ``type_value_map`` spreads it and adds only its own wording:
# ``type_value_map={**TYPE_VALUE_MAP, "Wheelie Bin": wt.RECYCLABLES}``.
TYPE_VALUE_MAP: dict[str, wt.WasteType] = {
    "Landfill": wt.GENERAL_WASTE,
    "Landfill Waste": wt.GENERAL_WASTE,
    "Organics": wt.ORGANIC,
    "Organics Waste": wt.ORGANIC,
    "Food and Garden Waste": wt.ORGANIC,
    "Food and Garden Organics": wt.ORGANIC,
    "Food and Green Waste": wt.ORGANIC,
    "Green Organics": wt.GARDEN_WASTE,
    "Garden Organics": wt.GARDEN_WASTE,
}


class OpenCitiesResult(NamedTuple):
    """What :class:`OpenCitiesRetriever` hands the parser.

    Besides the ``wasteservices`` reply it carries the argument a "no service
    for this property" answer should be blamed on, and the value the visitor
    gave for it, so the config flow flags the field they actually filled in.
    """

    response: Response
    argument: str
    value: str


# --------------------------------------------------------------------------- #
# Retriever
# --------------------------------------------------------------------------- #


class OpenCitiesRetriever(RetrieverFunc):
    """Resolve an address (or a geolocation id) to its ``wasteservices`` reply.

    Give the address one of two ways:

    * ``address``: the ``source.params`` field holding the whole address as
      free text (the default, ``"address"``);
    * ``address_template``: a ``str.format`` template over ``source.params``,
      for a council whose config splits the address into parts
      (``"{street_number} {street_name} {suburb} NSW {post_code}"``). Name the
      field a failed lookup should blame with ``argument``.

    ``geolocation_id`` names a param carrying the id directly, which skips the
    search (for a property the address search cannot find) and takes precedence
    over the address when both are given. A source offering only the id passes
    ``address=None``. A source offering both declares both params optional, and
    a fetch with neither raises ``SourceArgumentExceptionMultiple``.

    Args:
        domain: council base URL, e.g. ``"https://www.ballina.nsw.gov.au"``.
        address: ``source.params`` field with the address, or ``None``.
        address_template: ``str.format`` template over ``source.params``.
        argument: the param blamed when the address is not found (defaults to
            ``address``).
        geolocation_id: ``source.params`` field with a geolocation id.
        normalise: ``callable(address) -> address`` applied to the address
            before it is searched, for a council whose search is picky about
            the wording it accepts.
        search_fuzzy: use ``/api/v1/myarea/searchfuzzy`` instead of ``search``.
        max_results: optional ``maxresults`` query parameter on the search.
        page_link: optional ``pageLink`` query parameter some deployments
            require on the ``wasteservices`` call.
        ocsvclang: the ``ocsvclang`` query parameter.
        warm_up_url: a page fetched once per source before the API is used
            (cookie priming).
        warm_up_before: fire the warm-up before the address ``"search"``
            (default), or just before ``"wasteservices"``, which also covers
            the direct geolocation-id path where no search happens.
        headers: request headers. ``Accept: application/json`` is sent unless
            given: without an explicit Accept the search endpoint answers XML.
        strict_address_matching: by default the first (highest-ranked) search
            hit is used, trusting the API's relevance ranking. When True,
            several hits are instead disambiguated by exact (case- and
            space-insensitive) match against ``AddressSingleLine``, raising
            ``SourceArgAmbiguousWithSuggestions`` when that is not conclusive.
            Only for councils whose search ranks poorly enough that the first
            hit is often another property: for most it turns a correct hit
            that is merely worded differently (a missing state abbreviation)
            into a hard failure.
        strict_single_result: with ``strict_address_matching``, also hold a
            lone hit to the exact match. A few deployments answer an unrelated
            query with exactly one wrong hit (Lake Macquarie returns "2 Lake
            Ridge Lane, MURRAYS BEACH" for "2 Wallarah Rd"), and the caller is
            then offered it as a suggestion rather than handed another
            property's bins.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        domain: str,
        *,
        address: str | None = "address",
        address_template: str | None = None,
        argument: str | None = None,
        geolocation_id: str | None = None,
        normalise: Callable[[str], str] | None = None,
        search_fuzzy: bool = False,
        max_results: int | None = None,
        page_link: str | None = None,
        ocsvclang: str = "en-AU",
        warm_up_url: str | None = None,
        warm_up_before: Literal["search", "wasteservices"] = "search",
        headers: Mapping[str, str] | None = None,
        strict_address_matching: bool = False,
        strict_single_result: bool = False,
        timeout: int = 30,
    ):
        self.domain = domain.rstrip("/")
        self.address = address
        self.address_template = address_template
        self.argument = argument or address
        self.geolocation_id = geolocation_id
        self.normalise = normalise
        self.search_fuzzy = search_fuzzy
        self.max_results = max_results
        self.page_link = page_link
        self.ocsvclang = ocsvclang
        self.warm_up_url = warm_up_url
        self.warm_up_before = warm_up_before
        self.headers = _with_default_accept(headers)
        self.strict_address_matching = strict_address_matching
        self.strict_single_result = strict_single_result
        self.timeout = timeout
        # Per source, so a source polled repeatedly searches once, and warms up
        # once. Weak, so a discarded source takes its entries with it.
        self._resolved: WeakKeyDictionary[BaseSource, str] = WeakKeyDictionary()
        self._warmed: WeakSet[BaseSource] = WeakSet()

    def __call__(self, source: BaseSource) -> OpenCitiesResult:  # type: ignore[override]
        direct = self.geolocation_id and source.params.get(self.geolocation_id)
        if direct:
            assert self.geolocation_id is not None
            response = self._wasteservices(source, str(direct))
            return OpenCitiesResult(response, self.geolocation_id, str(direct))

        address = self._address(source)
        assert self.argument is not None
        cached = self._resolved.get(source)
        geolocation_id = cached or self._resolve(source, address)
        response = self._wasteservices(source, geolocation_id)
        if cached and not holds_services(response):
            # An id that once worked has gone stale: resolve it afresh, once.
            geolocation_id = self._resolve(source, address)
            response = self._wasteservices(source, geolocation_id)
        self._resolved[source] = geolocation_id
        return OpenCitiesResult(response, self.argument, address)

    # ---- request flow ---------------------------------------------------

    def _address(self, source: BaseSource) -> str:
        if self.address_template is not None:
            text = self.address_template.format(**source.params)
        else:
            value = source.params.get(self.address) if self.address else None
            if not value:
                fields = [f for f in (self.address, self.geolocation_id) if f]
                raise SourceArgumentExceptionMultiple(
                    fields, f"Either {' or '.join(fields)} must have a value"
                )
            text = str(value)
        text = " ".join(text.split())
        return self.normalise(text) if self.normalise else text

    def _resolve(self, source: BaseSource, address: str) -> str:
        if self.warm_up_before == "search":
            self._warm_up(source)
        return self._select(address, self._search(source, address))

    def _search(self, source: BaseSource, address: str) -> list[dict[str, Any]]:
        path = "searchfuzzy" if self.search_fuzzy else "search"
        params: dict[str, Any] = {"keywords": address}
        if self.max_results is not None:
            params["maxresults"] = self.max_results
        response = self._get(source, f"{self.domain}/api/v1/myarea/{path}", params)
        try:
            return response.json().get("Items") or []
        except ValueError:
            # A few legacy deployments answer the search with XML.
            return _search_items_from_xml(response.text)

    def _wasteservices(self, source: BaseSource, geolocation_id: str) -> Response:
        if self.warm_up_before == "wasteservices":
            self._warm_up(source)
        params: dict[str, str] = {
            "geolocationid": geolocation_id,
            "ocsvclang": self.ocsvclang,
        }
        if self.page_link:
            params["pageLink"] = self.page_link
        return self._get(source, f"{self.domain}{_WASTESERVICES_PATH}", params)

    def _warm_up(self, source: BaseSource) -> None:
        if not self.warm_up_url or source in self._warmed:
            return
        self._get(source, self.warm_up_url)
        self._warmed.add(source)

    def _get(
        self, source: BaseSource, url: str, params: dict[str, Any] | None = None
    ) -> Response:
        response = source.session.get(
            url, params=params, headers=self.headers, timeout=self.timeout
        )
        response.raise_for_status()
        return response

    def _select(self, address: str, items: list[dict[str, Any]]) -> str:
        """Pick the geolocation id of the search hit that is the address."""
        assert self.argument is not None
        if not items:
            raise SourceArgumentNotFound(self.argument, address)
        if not self.strict_address_matching:
            return items[0]["Id"]
        if len(items) == 1 and not self.strict_single_result:
            return items[0]["Id"]

        normalised = address.lower().replace(" ", "")
        exact = [
            item
            for item in items
            if item.get("AddressSingleLine", "").lower().replace(" ", "") == normalised
        ]
        if len(exact) == 1:
            return exact[0]["Id"]

        if not any(item.get("AddressSingleLine") for item in items):
            # No address text to disambiguate with (legacy XML hits): fall back
            # to the first hit rather than crash.
            return items[0]["Id"]

        suggestions = [item.get("AddressSingleLine", item["Id"]) for item in items]
        raise SourceArgAmbiguousWithSuggestions(self.argument, address, suggestions)


def _with_default_accept(headers: Mapping[str, str] | None) -> dict[str, str]:
    merged = dict(headers or {})
    if not any(name.lower() == "accept" for name in merged):
        merged["Accept"] = "application/json"
    return merged


def _search_items_from_xml(text: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(text, "xml")
    items: list[dict[str, Any]] = []
    for result in soup.find_all("PhysicalAddressSearchResult"):
        id_element = result.find("Id")
        if id_element and id_element.text.strip():
            item: dict[str, Any] = {"Id": id_element.text.strip()}
            address_element = result.find("AddressSingleLine")
            if address_element and address_element.text.strip():
                item["AddressSingleLine"] = address_element.text.strip()
            items.append(item)
    return items


def holds_services(response: Response) -> bool:
    """Whether a ``wasteservices`` reply carries any service HTML.

    A reply that is not JSON at all counts as holding services: that is the
    parser's to report as a changed response, not a reason to search again.
    """
    try:
        data = response.json()
    except ValueError:
        return True
    return bool(data.get("success", True) and data.get("responseContent"))


# --------------------------------------------------------------------------- #
# Parser
# --------------------------------------------------------------------------- #

# "5th Oct - 13th Oct." (the day, then a month name)
_WINDOW_RE = re.compile(
    r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,})",  # codespell:ignore nd
    re.IGNORECASE,
)
# "Mon 7/9/2026"
_NUMERIC_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_YEAR_RE = re.compile(r"(20\d{2})")


class OpenCitiesParser(Parser["list[dict[str, Any]]"]):
    """Read the ``wasteservices`` HTML into one record per dated service.

    Each record is ``{"type": <h3 text>, "date": <date>, "note": <text or
    None>}``. The note is the only place a service's cadence and kerbside
    instructions appear (the API returns one date per service), so it is
    carried through for the transformer's ``description_key``.

    A property the council holds no service for (vacant land, a lot not yet on
    a run) is reported as ``SourceArgumentNotFound`` on the argument the
    visitor filled in, rather than as an empty schedule.

    Args:
        date_format: ``strptime`` format of the ``.next-service`` text. A
            deployment describing a recurring service as "Every <Weekday>"
            instead of a concrete date is resolved to the next such weekday.
        require_date_precise: only read blocks also carrying a
            ``date-precise`` CSS class, skipping vague/recurring entries with
            no concrete next date (Shoalhaven mixes both kinds in one reply).
        exclude_type_prefixes: drop blocks whose heading starts with one of
            these. Some deployments list a "Calendar - Zone 14" link to
            download the calendar beside the services, and where it carries a
            date (the next occurrence of the service it links to) it would list
            that service twice. Its number varies per address, so it cannot be
            dropped by mapping it to ``None`` in the transformer's
            ``type_value_map``, which is the way to drop a heading known exactly.
        approximate_dates: for a service dated as a window ("5th Oct - 13th
            Oct.") rather than a day, take the window's first day, the year
            coming from the note ("Verge Collection 2026-2027") or, failing
            that, from the next occurrence. Gosnells reports verge collections
            this way.
    """

    def __init__(
        self,
        *,
        date_format: str = DEFAULT_DATE_FORMAT,
        require_date_precise: bool = False,
        exclude_type_prefixes: tuple[str, ...] = (),
        approximate_dates: bool = False,
    ):
        self.date_format = date_format
        self.require_date_precise = require_date_precise
        self.exclude_type_prefixes = exclude_type_prefixes
        self.approximate_dates = approximate_dates

    def __call__(
        self, raw: OpenCitiesResult, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        source_name = response_shape.source_name(source)
        try:
            data = raw.response.json()
        except ValueError:
            response_shape.expect(
                False,
                source_name=source_name,
                detail="the wasteservices reply is not JSON",
                raw=raw.response.text,
            )
        response_shape.expect(
            isinstance(data, dict),
            source_name=source_name,
            detail="the wasteservices reply is not a JSON object",
            raw=data,
        )
        if not data.get("success", True) or not data.get("responseContent"):
            # The address resolved, but the council holds no waste service for
            # that property. Name the address the visitor gave rather than the
            # internal geolocation GUID, unless the GUID is what they gave.
            raise SourceArgumentNotFound(
                raw.argument,
                raw.value,
                "The council lists no waste collection service for this "
                "property. Check the address, or contact the council if it "
                "should have a collection.",
            )

        soup = BeautifulSoup(data["responseContent"], "html.parser")
        selector = (
            "div.waste-services-result.date-precise"
            if self.require_date_precise
            else "article, div.waste-services-result"
        )
        today = datetime.date.today()
        records: list[dict[str, Any]] = []
        for block in _top_level(soup, selector):
            title = block.select_one("h3")
            next_service = block.select_one(".next-service")
            if title is None or next_service is None:
                continue
            waste_type = title.get_text(" ", strip=True)
            if waste_type.startswith(self.exclude_type_prefixes):
                continue
            date_text = next_service.get_text(" ", strip=True)
            if not date_text:
                continue
            note_element = block.select_one(".note")
            note = note_element.get_text(" ", strip=True) if note_element else None
            date = self._date(date_text, note or "", today)
            if date is None:
                continue
            records.append({"type": waste_type, "date": date, "note": note})
        return records

    def _date(self, text: str, note: str, today: datetime.date) -> datetime.date | None:
        try:
            return datetime.datetime.strptime(text, self.date_format).date()
        except ValueError:
            pass
        # A recurring service described as "Every <Weekday>" carries no date at
        # all: resolve it to the next occurrence of that weekday.
        parts = text.split()
        if len(parts) >= 2 and parts[0].lower() == "every":
            weekday = recurrence.weekday(parts[1])
            return None if weekday is None else recurrence.next_weekday(weekday)
        if self.approximate_dates:
            return _approximate_date(text, note, today)
        return None


def _top_level(soup: BeautifulSoup, selector: str) -> list[Tag]:
    """``soup.select()``, dropping matches nested inside another match.

    Some deployments wrap a matching ``<article>`` inside a matching
    ``div.waste-services-result`` (or the reverse); selecting both would
    otherwise count every entry twice.
    """
    candidates = soup.select(selector)
    candidate_ids = {id(candidate) for candidate in candidates}
    return [
        candidate
        for candidate in candidates
        if not any(id(parent) in candidate_ids for parent in candidate.parents)
    ]


def _month(name: str) -> int | None:
    """A month by full name, or by its three-letter abbreviation ("Oct").

    ``recurrence.month`` knows the full names only, and a window such as
    "5th Oct - 13th Oct." abbreviates them.
    """
    month = recurrence.month(name)
    if month is not None:
        return month
    try:
        return datetime.datetime.strptime(name[:3], "%b").month
    except ValueError:
        return None


def _approximate_date(
    text: str, note: str, today: datetime.date
) -> datetime.date | None:
    """The first day of a service dated "5th Oct - 13th Oct." (or numerically).

    The year appears only in the note ("Verge Collection 2026-2027"). A note
    naming one year is taken at its word even if that collection has already
    been and gone: verge weeks move from year to year, so rolling a past date
    forward would invent a date the council has not published. Only a note
    naming a span, or no year at all, leaves a real choice, and that is the
    first occurrence that has not passed.
    """
    numeric = _NUMERIC_DATE_RE.search(text)
    if numeric:
        try:
            return datetime.date(
                int(numeric.group(3)), int(numeric.group(2)), int(numeric.group(1))
            )
        except ValueError:
            return None

    window = _WINDOW_RE.search(text)
    if not window:
        return None
    day = int(window.group(1))
    month = _month(window.group(2))
    if month is None:
        return None

    years = sorted({int(year) for year in _YEAR_RE.findall(note)})
    if not years:
        years = [today.year, today.year + 1]
    candidates = []
    for year in years:
        try:
            candidates.append(datetime.date(year, month, day))
        except ValueError:
            continue
    future = [candidate for candidate in candidates if candidate >= today]
    if future:
        return min(future)
    return max(candidates) if candidates else None


# --------------------------------------------------------------------------- #
# Preprocessor
# --------------------------------------------------------------------------- #

_FORTNIGHTLY_RE = re.compile(r"fortnight", re.IGNORECASE)
# "Collected weekly" as well as "same day each week"; not "bi-weekly".
_WEEKLY_RE = re.compile(
    r"same day each week|\b(?:every|each) week\b|(?<![\w-])weekly\b", re.IGNORECASE
)


class OpenCitiesProjection(Preprocessor[Any, "dict[str, Any]"]):
    """Project each service's next date forward at the cadence its note states.

    The API returns only the next date per service, but the note usually says
    how often it recurs ("Collected fortnightly", "Same day each week"). Each
    record is passed through, followed by the later occurrences that fall
    within ``weeks`` of it. A note stating no cadence adds nothing.

    Args:
        weeks: how far ahead of the next date to project.
        when: ``source.params`` field (a ``boolean()``) that switches the
            projection on; without it the projection is always on.
    """

    def __init__(self, *, weeks: int = 4, when: str | None = None):
        self.weeks = weeks
        self.when = when

    def __call__(
        self, records: Iterable[dict[str, Any]], source: BaseSource | None = None
    ) -> Iterable[dict[str, Any]]:
        enabled = self.when is None or (source is not None and source.params[self.when])
        for record in records:
            yield record
            if not enabled:
                continue
            note = record.get("note") or ""
            if _FORTNIGHTLY_RE.search(note):
                step = 2
            elif _WEEKLY_RE.search(note):
                step = 1
            else:
                continue
            for occurrence in range(1, self.weeks // step):
                yield {
                    **record,
                    "date": record["date"]
                    + datetime.timedelta(weeks=step * occurrence),
                }
