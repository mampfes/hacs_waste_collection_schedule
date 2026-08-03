"""api.phila.gov: the City of Philadelphia's address index and holiday calendar.

The city runs two open endpoints a collection schedule is assembled from, and
neither is a schedule:

* **AIS** (``/ais/v1/addresses/...``) answers an address query with a ranked
  ``features`` collection. The matched property's ``properties`` carry the
  weekdays its rounds are collected on, as ``"MON"``/``"TUE"`` strings, but no
  dates at all: the cadence is simply weekly, so the dates are projected.
* **Trash Day** (``/phila/trashday/v1``) publishes the city's *observed* holiday
  dates. Using them rather than the ``holidays`` library matters, because the
  schedule slides by what the city observes, not by the federal calendar.

The two shapes below are what a source on this API composes: the parser that
picks the matched property out of AIS, and the preprocessor that applies the
city's published holiday rule to already-projected rows::

    retrieve = retrievers.LegacyHttpGetRetriever(url=..., headers=PhilaGov.HEADERS)
    parse = PhilaGov.AddressPropertiesParser()
    preprocess = Compose(
        RecurrenceExpander(_describe),
        PhilaGov.HolidayCascadeShift(),
        Deduplicate(),
    )

Plain ``requests`` rather than the shared curl_cffi session: api.phila.gov
answers the impersonated-Chrome client with a 202 bot challenge.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import requests

from waste_collection_schedule import date_parsers
from waste_collection_schedule.preprocessors import Preprocessor

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.parsers import Response

ADDRESS_URL = "https://api.phila.gov/ais/v1/addresses/{address}"
HOLIDAYS_URL = "https://api.phila.gov/phila/trashday/v1"
HEADERS = {"user-agent": "Mozilla/5.0"}

_parse_iso = date_parsers.for_format("%Y-%m-%d")


class AddressPropertiesParser:
    """The property record AIS matched, as a single-record list.

    AIS ranks its matches, so an address that resolves at all resolves best at
    ``features[0]``: that is the property the city's own collection-day page
    shows. A query that matched nothing yields no records, so pair this with
    ``RAISE_ON_EMPTY`` and the user is told their address did not resolve.
    """

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[Mapping[str, Any]]:
        features = response.json().get("features") or []
        return [features[0]["properties"]] if features else []


def observed_holidays(
    *,
    url: str = HOLIDAYS_URL,
    headers: Mapping[str, str] = HEADERS,
    timeout: int = 30,
) -> list[datetime.date]:
    """Every date the city publishes as an observed holiday."""
    response = requests.get(url, headers=dict(headers), timeout=timeout)
    return [_parse_iso(item["start_date"]) for item in response.json()["holidays"]]


def shift_within_week(
    holidays: Sequence[datetime.date], collection_date: datetime.date
) -> datetime.date:
    """The city's rule: a collection slips a day per holiday earlier in its week.

    Weeks run Monday to Sunday. Each holiday falling in the collection's own
    week, on or before the collection day, pushes it back one day; if the day it
    lands on is itself a holiday, the rule applies again.
    """
    week_start = collection_date - datetime.timedelta(days=collection_date.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    week_holidays = sorted(h for h in holidays if week_start <= h <= week_end)
    shift = sum(1 for h in week_holidays if h <= collection_date)
    adjusted = collection_date + datetime.timedelta(days=shift)
    if adjusted in holidays and adjusted != collection_date:
        return shift_within_week(holidays, adjusted)
    return adjusted


class HolidayCascadeShift(Preprocessor):
    """Slide projected ``(date, key)`` rows by the city's holiday rule.

    Reads the observed-holiday calendar once per fetch, then applies
    :func:`shift_within_week` to every row. Put it after the cadence projection
    and before a :class:`~waste_collection_schedule.preprocessors.Deduplicate`,
    since two collections in one week can be pushed onto the same day.

    Args:
        url: the observed-holiday feed.
        headers: headers for that request.
        timeout: request timeout in seconds.
        weekdays_only: ignore a holiday falling at a weekend (default True).
            Nothing is collected then, so such a holiday moves nothing, and
            counting it would push the following week's collections a day late.
    """

    def __init__(
        self,
        *,
        url: str = HOLIDAYS_URL,
        headers: Mapping[str, str] = HEADERS,
        timeout: int = 30,
        weekdays_only: bool = True,
    ):
        self._url = url
        self._headers = headers
        self._timeout = timeout
        self._weekdays_only = weekdays_only

    def __call__(
        self, records: Any, source: BaseSource | None = None
    ) -> Iterable[tuple[datetime.date, str]]:
        holidays = observed_holidays(
            url=self._url, headers=self._headers, timeout=self._timeout
        )
        if self._weekdays_only:
            holidays = [h for h in holidays if h.weekday() < 5]
        for collection_date, key in records:
            yield shift_within_week(holidays, collection_date), key
