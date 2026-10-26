from datetime import date, timedelta
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.transformers import RowTransformer


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _delay_holidays(year: int) -> list[date]:
    """Holidays after which LA Sanitation delays collection by one day.

    See https://sanitation.lacity.gov/services/lasan-holiday-collection-delays
    Holidays on a weekend cause no delay, so they are ignored by the caller.
    """
    return [
        date(year, 1, 1),  # New Year's Day
        date(year, 7, 4),  # Independence Day
        _nth_weekday(year, 9, 0, 1),  # Labor Day
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving
        date(year, 12, 25),  # Christmas Day
    ]


def _apply_holiday_delay(collection_date: date) -> date:
    """Shift a regular collection date by one day if a weekday holiday
    occurred earlier in the same week (or on the collection day itself)."""
    week_start = collection_date - timedelta(days=collection_date.weekday())
    for holiday in _delay_holidays(collection_date.year):
        if holiday.weekday() < 5 and week_start <= holiday <= collection_date:
            return collection_date + timedelta(days=1)
    return collection_date


def _schedule(record, source):
    if source is None:
        raise ValueError("Address lookup requires a source")
    address = source.params["street_address"]
    if not address:
        raise SourceArgumentRequired(
            "street_address", "Enter a Los Angeles street address"
        )
    if record.get("status") != "exactMatch":
        raise SourceArgumentNotFound("street_address", address)
    day = record["layers"]["merge"]["day"]
    weekday = recurrence.weekday(day)
    if weekday is None or weekday > 4:
        raise ValueError(f"Unknown Los Angeles collection day: {day!r}")
    today = date.today()
    for key in ("BLACK BIN", "BLUE BIN", "GREEN BIN"):
        yield preprocessors.Schedule(
            key,
            recurrence.next_weekday(weekday, on_or_after=today - timedelta(days=1)),
            until=today + timedelta(days=13),
        )


def _holiday(collection_date, _key, _source):
    shifted = _apply_holiday_delay(collection_date)
    return shifted if shifted >= date.today() else None


@final
class Source(BaseSource):
    TITLE = "City of Los Angeles, CA"
    DESCRIPTION = "Source script for Los Angeles, California waste collection services"
    URL = "https://www.lacitysan.org"
    COUNTRY = "us"
    TEST_CASES: ClassVar[dict] = {
        "East Valley District Yard": {"street_address": "11050 Pendleton Street"},
        "West Valley District Yard": {"street_address": "8840 Vanalden Avenue"},
        "North Central District Yard": {
            "street_address": "452 North San Fernando Road"
        },
        "South Los Angeles District Yard": {"street_address": "786 South Mission Road"},
        "Harbor District Yard": {"street_address": "1400 North Gaffey Street"},
        "West Los Angeles District Yard": {"street_address": "2027 Stoner Avenue"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Missing address": {"street_address": ""},
        "Unknown address": {"street_address": "zzzz invalid address 999999"},
    }
    PARAMS = (street_address("street_address"),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.ORGANIC]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your complete street address within Los Angeles city limits, without city/state. The official GeoQuery API supplies the collection weekday. Black, blue and green bins share this day; the existing LASAN holiday delays are applied. Since the v3 migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        "https://api.lacity.org/boe_geoquery/addressvalidationservice",
        params=lambda street_address, **_: {
            "address": street_address,
            "status": "new",
            "layerset": "neighborhoodinfo",
            "apikey": "YsvfDePjTDKtLl041Vz25jCbfjExMtCh",  # Public website API key
        },
    )
    parse = parsers.JsonParser()
    preprocess = preprocessors.Compose(
        preprocessors.DefaultPreprocessor(),
        preprocessors.RecurrenceExpander(_schedule),
        preprocessors.HolidayShift(_holiday),
        preprocessors.SortRows(),
    )
    transform = RowTransformer(
        type_value_map={
            "BLACK BIN": wt.GENERAL_WASTE,
            "BLUE BIN": wt.RECYCLABLES,
            "GREEN BIN": wt.ORGANIC,
        }
    )
