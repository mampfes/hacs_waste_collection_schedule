"""INFEO (infeo.at) -- a shared multi-tenant waste-calendar platform.

Demonstrates: a hosted platform serving several unrelated municipal/private
waste providers under one API (``services.infeo.at/awm/api/<customer>/...``),
each publishing one or more calendar years that must be queried individually
-- either by a named collection zone, or by resolving a city/street/house
number cascade -- and unioned into the full schedule. A year for which the
configured zone/address isn't found is skipped (the site republishes with
gaps around a boundary year) rather than failing the whole fetch. No
configured retriever expresses "resolve then fetch, once per published year,
via one of two alternative lookup paths", hence a source-defined
retrieve()/parse() pair. ``alternatives()`` now enforces that exactly one of
the zone path or the city/street/house-number path is supplied, replacing the
legacy code's crash (a bare ``None in ...`` TypeError) when neither was.
"""

import logging
from typing import ClassVar, final

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
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_LOGGER = logging.getLogger(__name__)


def _fetch_by_zone(session, base_url: str, calendar_id, calendar_name, zone: str):
    r = session.get(f"{base_url}/zones", params={"calendarId": calendar_id})
    r.raise_for_status()
    zones = r.json()
    if not zones:
        _LOGGER.warning(
            "no zones found for calendar year %s, continuing with next calendar year ...",
            calendar_name,
        )
        return None

    zone_id = next((z["id"] for z in zones if zone in z["name"]), None)
    if zone_id is None:
        _LOGGER.warning(
            "zone '%s' not found in calendar year %s, continuing with next calendar year ...",
            zone,
            calendar_name,
        )
        return None

    r = session.get(
        f"{base_url}/v2/export",
        params={"calendarId": calendar_id, "zoneId": zone_id, "outputType": "ical"},
    )
    r.raise_for_status()
    return r


def _fetch_by_address(
    session,
    base_url: str,
    calendar_id,
    calendar_name,
    city_name: str,
    street_name: str,
    housenumber: str,
):
    r = session.get(f"{base_url}/cities", params={"calendarId": calendar_id})
    r.raise_for_status()
    cities = r.json()
    if not cities:
        _LOGGER.warning(
            "no cities found for calendar year %s, continuing with next calendar year ...",
            calendar_name,
        )
        return None
    city_id = next((c["id"] for c in cities if city_name in c["name"]), None)
    if city_id is None:
        _LOGGER.warning(
            "city '%s' not found in calendar year %s, continuing with next calendar year ...",
            city_name,
            calendar_name,
        )
        return None

    r = session.get(
        f"{base_url}/streets",
        params={"calendarId": calendar_id, "cityId": city_id},
    )
    r.raise_for_status()
    streets = r.json()
    if not streets:
        _LOGGER.warning(
            "no streets found for calendar year %s, continuing with next calendar year ...",
            calendar_name,
        )
        return None
    street_id = next((s["id"] for s in streets if street_name in s["name"]), None)
    if street_id is None:
        _LOGGER.warning(
            "street '%s' not found in calendar year %s, continuing with next calendar year ...",
            street_name,
            calendar_name,
        )
        return None

    r = session.get(
        f"{base_url}/housenumbers",
        params={"calendarId": calendar_id, "streetId": street_id},
    )
    r.raise_for_status()
    housenumbers = r.json()
    if not housenumbers:
        _LOGGER.warning(
            "no housenumbers found for calendar year %s, continuing with next calendar year ...",
            calendar_name,
        )
        return None
    # The API's "housenumbers" endpoint returns plain strings, not objects with
    # their own id -- the configured value itself is the id once matched.
    matched = next((hn for hn in housenumbers if housenumber in hn), None)
    if matched is None:
        _LOGGER.warning(
            "housenumber '%s' not found in calendar year %s, continuing with next calendar year ...",
            housenumber,
            calendar_name,
        )
        return None

    r = session.get(
        f"{base_url}/v2/export",
        params={
            "calendarId": calendar_id,
            "cityId": city_id,
            "streetId": street_id,
            "housenumber": housenumber,
            "outputType": "ical",
        },
    )
    r.raise_for_status()
    return r


@final
class Source(BaseSource):
    TITLE = "infeo"
    DESCRIPTION = "Source for INFEO waste collection."
    URL = "https://www.infeo.at/"
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

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

    def retrieve(self, source):
        session = source.session
        customer = source.params["customer"]
        zone = source.params.get("zone")
        city_name = source.params.get("city")
        street_name = source.params.get("street")
        housenumber = source.params.get("housenumber")

        base_url = f"https://services.infeo.at/awm/api/{customer}/wastecalendar"

        years_resp = session.get(
            f"{base_url}/calendars", params={"showUnpublishedCalendars": "false"}
        )
        if years_resp.status_code == 500:
            raise SourceArgumentNotFound("customer", customer)
        years_resp.raise_for_status()

        calendar_years = years_resp.json()
        if not calendar_years:
            raise SourceArgumentNotFound(
                "customer", customer, "no calendars are published for this customer."
            )

        responses = []
        for calendar_year in calendar_years:
            calendar_id = calendar_year["id"]
            calendar_name = calendar_year["name"]
            if zone is not None:
                ical = _fetch_by_zone(
                    session, base_url, calendar_id, calendar_name, zone
                )
            else:
                ical = _fetch_by_address(
                    session,
                    base_url,
                    calendar_id,
                    calendar_name,
                    city_name,
                    street_name,
                    housenumber,
                )
            if ical is not None:
                responses.append(ical)
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

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
