"""blupassionsystem.de "City App" waste calendars (DE).

Municipal apps of the blupassion platform share one REST backend, one numeric
``appId`` per app. An address narrows one level at a time through
``garbageregion/filterRegion``: every POST carries the ids resolved so far and
answers the options of the next levels::

    region -> city -> part of city -> street -> house number

A level the address does not have answers an empty list and is skipped; a level
it has must be given. ``garbageorte/getAllGarbageCalendar`` then answers the
calendars of the narrowest id. A calendar is a rule, not a list of dates: a start
(``fromDate``, epoch milliseconds), an optional end (``toDate``) and a
``frequency`` in days. ``holidayViews`` lists the collections that move, as
``holiday`` (the day it would fall on) and ``shiftTo``.

``BlupassionApp`` declares the lookups for ``retrievers.LookupChainRetriever``
and ``BlupassionParser`` expands the rules, applying the holiday moves.
"""

import datetime
import logging
from collections.abc import Callable, Iterable
from typing import Any
from zoneinfo import ZoneInfo

from waste_collection_schedule import recurrence
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup

_LOGGER = logging.getLogger(__name__)

_REST = "https://blupassionsystem.de/city/rest"
_FILTER_URL = f"{_REST}/garbageregion/filterRegion"
_CALENDAR_URL = f"{_REST}/garbageorte/getAllGarbageCalendar"
_TZ = ZoneInfo("Europe/Berlin")


def _norm(value: Any) -> str:
    return str(value).lower().replace(" ", "").replace("-", "")


def _choose(
    options: list[dict] | None, argument: str, wanted: Any, label: str
) -> int | None:
    """The id of the option named ``wanted``, or ``None`` where there is no level."""
    if not options:
        if wanted is not None:
            _LOGGER.warning("%s provided but not needed", argument)
        return None
    if wanted is None:
        raise SourceArgumentRequired(
            argument, f"{label} must be selected from the available options"
        )
    for option in options:
        if _norm(option["name"]) == _norm(wanted):
            return option["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        argument, wanted, [str(option["name"]) for option in options]
    )


class BlupassionApp:
    """One blupassion app: its ``app_id`` and the names of the address fields.

    Args:
        app_id: the ``appId`` the app's requests carry.
        city, part_of_city, street, house_number: the source parameters holding
            each address level (``part_of_city``, ``street`` and
            ``house_number`` are optional).
    """

    def __init__(
        self,
        app_id: int,
        *,
        city: str,
        part_of_city: str,
        street: str,
        house_number: str,
    ):
        self.app_id = app_id
        self._fields = (city, part_of_city, street, house_number)

    def body(self, region=None, city=None, part=None, street=None, house=None) -> dict:
        """The request body for the ids resolved so far (a house number is a street id)."""
        return {
            "active": True,
            "appId": self.app_id,
            "hugeDataInfo": "",
            "regionId": region,
            "cityId": city,
            "streetId": house if house is not None else street,
            "partOfCityId": part,
            "districtId": None,
        }

    def steps(self) -> tuple[Lookup, ...]:
        """The lookups resolving ``(region, city, part_of_city, street, house)``."""
        city_f, part_f, street_f, house_f = self._fields

        def region(response, **_):
            regions = response.json()["data"].get("regions")
            return regions[0]["id"] if regions else None

        def city(response, *_, **params):
            options = response.json()["data"]["citys"]
            return _choose(options, city_f, params[city_f], "A city")

        def level(key: str, field: str, label: str):
            def pick(response, *_, **params):
                return _choose(
                    response.json()["data"][key], field, params.get(field), label
                )

            return pick

        def lookup(pick: Callable) -> Lookup:
            return Lookup(
                _FILTER_URL,
                method="POST",
                json=lambda *keys, **_: self.body(*keys),
                pick=pick,
            )

        return (
            lookup(region),
            lookup(city),
            lookup(level("partOfCitys", part_f, "A district (Stadtteil)")),
            lookup(level("streets", street_f, "A street (Strasse)")),
            lookup(level("houseNumbers", house_f, "A house number (Nummer)")),
        )

    @staticmethod
    def calendar_url(*_, **__) -> str:
        return _CALENDAR_URL

    def calendar_params(self, *keys, **_) -> dict:
        """The calendar query: the ids and a window from yesterday for a year."""
        start = datetime.datetime.combine(
            datetime.date.today() - datetime.timedelta(days=1),
            datetime.time(),
            tzinfo=_TZ,
        )
        end = start + datetime.timedelta(days=365)
        # An unset level is left out of the query: serialised, None reads "None".
        return {
            **{k: v for k, v in self.body(*keys).items() if v is not None},
            "fromTime": int(start.timestamp() * 1000),
            "toTime": int(end.timestamp() * 1000),
        }


def _day(milliseconds: int) -> datetime.date:
    return datetime.datetime.fromtimestamp(milliseconds / 1000, _TZ).date()


class BlupassionParser(Parser["list[tuple[datetime.date, str]]"]):
    """Expand the calendars' day-frequency rules into ``(date, name)`` rows.

    Each calendar recurs every ``frequency`` days from ``fromDate`` until
    ``toDate`` (open-ended where missing), within a window from yesterday for a
    year. A collection that falls on a holiday moves to its ``shiftTo``.
    """

    def __call__(self, response, source=None) -> "list[tuple[datetime.date, str]]":
        data = response.json()["data"]
        if "calendars" not in data:
            raise ValueError("Unexpected response")
        window_start = datetime.date.today() - datetime.timedelta(days=1)
        window_end = window_start + datetime.timedelta(days=365)
        moves: dict[datetime.date, datetime.date] = {}
        for holiday in data.get("holidayViews") or []:
            # The list repeats each holiday once per tour; the first entry wins.
            moves.setdefault(_day(holiday["holiday"]), _day(holiday["shiftTo"]))

        rows: list[tuple[datetime.date, str]] = []
        for calendar in data["calendars"]:
            until = _day(calendar["toDate"]) if calendar["toDate"] else window_end
            dates: Iterable[datetime.date] = recurrence.recurring_within(
                _day(calendar["fromDate"]),
                datetime.timedelta(days=calendar["frequency"]),
                not_before=window_start,
                until=min(until, window_end),
            )
            rows.extend((moves.get(date, date), calendar["name"]) for date in dates)
        return rows
