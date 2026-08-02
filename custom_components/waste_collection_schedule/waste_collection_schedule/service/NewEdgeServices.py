"""New Edge Services customer portal: the holiday-delay table it publishes.

New Edge Services hosts the customer portal a hauler's residents look their
collection days up on. The portal is a single-page app, so its holiday calendar
is not served as data: it is compiled into the JS bundle the page loads, as a
per-community list of ``{service: HOLIDAYS, dates: [...]}`` entries, each with a
``skip`` flag saying whether that day's collection slides to the next day.

The schedule itself comes from wherever the hauler keeps it (an ArcGIS route
layer, for the one provider on this platform today). This module supplies only
the holiday overlay, as a preprocess stage that runs after the cadence has been
projected::

    preprocess = Compose(
        RecurrenceExpander(_describe),
        NewEdgeServices.HolidayDelayShift(community=_city),
    )
"""

from __future__ import annotations

import datetime
import logging
import re
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

import requests

from waste_collection_schedule.preprocessors import Preprocessor

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

PORTAL_URL = "https://support.newedgeservices.com/cwd/"

# <script src="/cwd/static/js/main.<hash>.js"> — the bundle the table lives in.
_BUNDLE_RE = r'<script[^>]+src=["\']((?:/[^"\']+)?/static/js/main\.[0-9a-f]+\.js)["\']'
# The HOLIDAYS block inside a community's entry, and one dated row within it.
_HOLIDAY_BLOCK_RE = r"service\s*:\s*Rt\.HOLIDAYS\s*,\s*dates\s*:\s*\[([^\]]+)\]"
_HOLIDAY_ROW_RE = (
    r'start\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?'
    r'end\s*:\s*At\(\)\(["\']([^"\']+)["\'].*?skip\s*:\s*!([01])'
)
# How far past a community's entry to keep reading when its list is unterminated.
_SEGMENT_LIMIT = 50000


def _iso(value: str) -> datetime.date | None:
    try:
        parts = value.split("-")
        return datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, TypeError, IndexError):
        return None


def holiday_delays(
    community: str, *, portal_url: str = PORTAL_URL, timeout: int = 15
) -> dict[str, int]:
    """The community's ``{ISO date: days delayed}`` table, or ``{}``.

    Best-effort by design: the table is scraped out of a JS bundle, so a portal
    that has been rebuilt in a shape this no longer recognises yields no
    adjustments rather than failing the whole fetch. The schedule is still
    correct on every non-holiday week, which is most of them.

    Args:
        community: the community name as the portal spells it, matched
            case-insensitively. This is typically the city a geocoder returned.
        portal_url: the hauler's portal landing page.
        timeout: per-request timeout in seconds.
    """
    origin = portal_url.split("/", 3)
    base = "/".join(origin[:3])
    try:
        page = requests.get(portal_url, timeout=timeout)
        page.raise_for_status()
        match = re.search(_BUNDLE_RE, page.text)
        if not match:
            _LOGGER.debug("No JS bundle found on the New Edge portal %s", portal_url)
            return {}
        bundle = requests.get(base + match.group(1), timeout=timeout)
        bundle.raise_for_status()
        script = bundle.text
    except requests.RequestException as err:
        _LOGGER.debug("Could not read the New Edge holiday table: %s", err)
        return {}

    entry = re.search(
        rf'["\']?{re.escape(community)}["\']?\s*:\s*\[', script, re.IGNORECASE
    )
    if not entry:
        return {}
    start = entry.start()
    terminator = re.search(r"\],", script[start:])
    end = (
        start + terminator.end()
        if terminator
        else min(len(script), start + _SEGMENT_LIMIT)
    )

    block = re.search(_HOLIDAY_BLOCK_RE, script[start:end])
    if not block:
        return {}

    delays: dict[str, int] = {}
    for start_str, end_str, skip_flag in re.findall(_HOLIDAY_ROW_RE, block.group(1)):
        # skip: !1 is JS for false-as-truthy-source, i.e. the day *is* skipped
        # and the collection slides one day. !0 means no adjustment.
        if skip_flag != "1":
            continue
        first = _iso(start_str)
        if first is None:
            continue
        last = _iso(end_str) if end_str else None
        if last is None or last < first:
            last = first
        current = first
        while current <= last:
            delays[current.isoformat()] = 1
            current += datetime.timedelta(days=1)
    return delays


class HolidayDelayShift(Preprocessor):
    """Slide ``(date, key)`` rows that land on a New Edge holiday.

    Loads the community's table once per fetch, then moves each affected
    collection forward by the days the portal says it slips.

    Args:
        community: the community name, or a ``callable(source) -> str`` reading
            it off the source (typically the city a geocode returned). An empty
            name means no table and no adjustments.
        portal_url: the hauler's portal landing page.
        timeout: per-request timeout in seconds.
    """

    def __init__(
        self,
        *,
        community: str | Callable[[Any], str],
        portal_url: str = PORTAL_URL,
        timeout: int = 15,
    ):
        self._community = community
        self._portal_url = portal_url
        self._timeout = timeout

    def __call__(
        self, records: Any, source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        name = self._community(source) if callable(self._community) else self._community
        delays = (
            holiday_delays(name, portal_url=self._portal_url, timeout=self._timeout)
            if name
            else {}
        )
        for collection_date, key in records:
            delay = delays.get(collection_date.isoformat())
            if delay:
                collection_date = collection_date + datetime.timedelta(days=delay)
            yield collection_date, key
