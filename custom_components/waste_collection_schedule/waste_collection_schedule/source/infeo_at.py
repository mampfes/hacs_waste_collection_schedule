"""INFEO (infeo.at) -- a shared multi-tenant waste-calendar platform.

Demonstrates: a hosted platform serving several unrelated municipal/private
waste providers under one API (``services.infeo.at/awm/api/<customer>/...``),
each publishing one or more calendar years that must be queried individually
-- either by a named collection zone, or by resolving a city/street/house
number cascade -- and unioned into the full schedule. A year for which the
configured zone/address isn't found is skipped (the site republishes with
gaps around a boundary year) rather than failing the whole fetch: that is a
FanOutRetriever whose ``prepare`` lists the published calendars and whose
fetch is a declared request, run after that year's own lookups, that is not
made (and returns ``None``) for a year this household is not in.
``alternatives()`` now enforces that exactly one of
the zone path or the city/street/house-number path is supplied, replacing the
legacy code's crash (a bare ``None in ...`` TypeError) when neither was.
"""

import logging
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    city,
    house_number,
    service_id,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import EachResponse, IcsParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.retrievers import FanOutRetriever, Lookup, Request
from waste_collection_schedule.transformers import ICSTransformer

_LOGGER = logging.getLogger(__name__)


def _base(customer: str) -> str:
    return f"https://services.infeo.at/awm/api/{customer}/wastecalendar"


def _published_years(response, customer: str, **_) -> list:
    """The customer's published calendar years, listed once."""
    if response.status_code == 500:
        raise SourceArgumentNotFound("customer", customer)
    response.raise_for_status()

    calendar_years = response.json()
    if not calendar_years:
        raise SourceArgumentNotFound(
            "customer", customer, "no calendars are published for this customer."
        )
    return calendar_years


def _find(what: str, name=lambda entry: entry["name"], found=None):
    """A pick: the id of the entry whose name contains the configured value.

    ``None`` when the year does not list it: such a year is skipped, not
    failed, because the site republishes with gaps around a boundary year.
    """

    def pick(response, calendar_year, *_keys, **params) -> object:
        entries = response.json()
        if not entries:
            _LOGGER.warning(
                "no %ss found for calendar year %s, continuing with next calendar year ...",
                what,
                calendar_year["name"],
            )
            return None
        value = params[what]
        match = next((entry for entry in entries if value in name(entry)), None)
        if match is None:
            _LOGGER.warning(
                "%s '%s' not found in calendar year %s, continuing with next calendar year ...",
                what,
                value,
                calendar_year["name"],
            )
            return None
        return found(match) if found is not None else match["id"]

    return pick


def _level(path: str, what: str, *, params, when, **pick) -> Lookup:
    """One per-year lookup below the customer's wastecalendar API."""
    return Lookup(
        lambda *_, customer, **__: f"{_base(customer)}/{path}",
        params=params,
        when=when,
        pick=_find(what, **pick),
    )


def _export_params(calendar_year, _years, zone_id, city_id, street_id, _number, **p):
    if p.get("zone") is not None:
        return {
            "calendarId": calendar_year["id"],
            "zoneId": zone_id,
            "outputType": "ical",
        }
    return {
        "calendarId": calendar_year["id"],
        "cityId": city_id,
        "streetId": street_id,
        "housenumber": p.get("housenumber"),
        "outputType": "ical",
    }


def _in_this_year(calendar_year, _years, zone_id, _city_id, _street_id, number, **p):
    """Whether the zone (or the address, down to its house number) was found."""
    return (zone_id if p.get("zone") is not None else number) is not None


# One year's ICS, or None when this household is not in that year: either the
# named zone, or the city -> street -> house number cascade, then the export.
_CALENDAR = Request(
    lambda *_, customer, **__: f"{_base(customer)}/v2/export",
    before=(
        _level(
            "zones",
            "zone",
            params=lambda calendar_year, *_, **__: {"calendarId": calendar_year["id"]},
            when=lambda *_, zone=None, **__: zone is not None,
        ),
        _level(
            "cities",
            "city",
            params=lambda calendar_year, *_, **__: {"calendarId": calendar_year["id"]},
            when=lambda *_, zone=None, **__: zone is None,
        ),
        _level(
            "streets",
            "street",
            params=lambda calendar_year, _years, _zone, city_id, **_: {
                "calendarId": calendar_year["id"],
                "cityId": city_id,
            },
            when=lambda _year, _years, _zone, city_id, **_: city_id is not None,
        ),
        # The API's "housenumbers" endpoint returns plain strings, not objects
        # with their own id -- the configured value itself is the id once
        # matched.
        _level(
            "housenumbers",
            "housenumber",
            params=lambda calendar_year, _years, _zone, _city, street_id, **_: {
                "calendarId": calendar_year["id"],
                "streetId": street_id,
            },
            when=lambda _year, _years, _zone, _city, street_id, **_: (
                street_id is not None
            ),
            name=lambda entry: entry,
            found=lambda entry: entry,
        ),
    ),
    when=_in_this_year,
    params=_export_params,
)


@final
class Source(BaseSource):
    TITLE = "infeo"
    DESCRIPTION = "Source for INFEO waste collection."
    URL = "https://www.infeo.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    REGIONS = (
        region(
            "Bogenschütz Entsorgung",
            url="https://bogenschuetz-entsorgung.de",
            country="de",
            customer="bogenschütz",
        ),
        region(
            "Innsbrucker Kommunalbetriebe",
            url="https://ikb.at",
            country="at",
            customer="ikb",
        ),
        region(
            "Stadt Salzburg",
            url="https://stadt-salzburg.at",
            country="at",
            customer="salzburg",
        ),
        region(
            "Abfallverband Schwechat",
            url="https://schwechat.umweltverbaende.at/",
            country="at",
            customer="av-schwechat",
        ),
    )

    TEST_CASES: ClassVar[dict] = {
        "Bogeschütz": {"customer": "bogenschütz", "zone": "Dettenhausen"},
        "ikb": {
            "customer": "ikb",
            "city": "Innsbruck",
            "street": "Achselkopfweg",
            "housenumber": "1",
        },
        "salzburg": {
            "customer": "salzburg",
            "city": "Salzburg",
            "street": "Adolf-Schemel-Straße",
            "housenumber": "13",
        },
        "Schwechat": {
            "customer": "av-schwechat",
            "city": "Fischamend",
            "street": "Am Damm",
            "housenumber": "2",
        },
    }

    PARAMS = (
        service_id(field="customer"),
        alternatives(
            [text_field("zone", "Zone")],
            [
                city(field="city"),
                street(field="street"),
                house_number(field="housenumber"),
            ],
        ),
    )

    retrieve = FanOutRetriever(
        prepare=Lookup(
            lambda customer, **_: f"{_base(customer)}/calendars",
            params={"showUnpublishedCalendars": "false"},
            raise_for_status=False,
            pick=_published_years,
        ),
        targets=lambda source, calendar_years: calendar_years,
        fetch=_CALENDAR,
    )

    parse = EachResponse(IcsParser())

    transform = ICSTransformer()

    def __init__(
        self,
        customer: str,
        zone: "str | None" = None,
        city: "str | None" = None,
        street: "str | None" = None,
        housenumber: "str | int | None" = None,
    ):
        super().__init__(
            customer=customer,
            zone=zone,
            city=city,
            street=street,
            housenumber=None if housenumber is None else str(housenumber),
        )
