"""PreZero waste collection calendar network (abfallkalender.prezero.network).

Composes: :class:`~waste_collection_schedule.retrievers.FanOutRetriever`. The
address is resolved once in the retriever's ``prepare`` step (a POST that 302s
to a URL carrying the street id, with an HTML meta-refresh fallback for
deployments that redirect that way instead), and the calendar is then split
across one ICS download per year, which is what the fan-out's targets are.
Both years are always fetched and both must succeed, so this is a fan-out over
a fixed target list rather than a
:class:`~waste_collection_schedule.retrievers.YearlyRetriever`, whose second
year is deliberately best-effort.
"""

import re
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.field_terms import CITY
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://abfallkalender.prezero.network"
_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
_META_REFRESH_RE = re.compile(r'url=[\'"]?([^\'" >]+)')
_STREET_ID_RE = re.compile(r"/calendar/(\d+)/")


def _resolve_street_id(source) -> str:
    """The fan-out's prepare step: address -> the site's own street id.

    The id is only ever handed back in the redirect target, so the redirect is
    read rather than followed. A deployment that redirects with an HTML
    meta-refresh instead of a ``Location`` header is read the same way.
    """
    street_name = source.params["street"]
    r = source.session.post(
        f"{_BASE_URL}/{source.params['city']}",
        data={"street": street_name, "houseNo": source.params["house_number"]},
        allow_redirects=False,
    )

    if r.status_code not in _REDIRECT_STATUSES:
        raise SourceArgumentNotFound(
            "street",
            street_name,
            "Street not found. Please verify the street name is correct and "
            "matches exactly as shown on the PreZero website.",
        )

    location = r.headers.get("Location")
    if not location and "http-equiv" in r.text and "refresh" in r.text.lower():
        match = _META_REFRESH_RE.search(r.text)
        if match:
            location = match.group(1)
    if not location:
        raise SourceArgumentNotFound(
            "street",
            street_name,
            "Could not determine calendar URL. Please verify your street and "
            "house number.",
        )

    match = _STREET_ID_RE.search(location)
    if not match:
        raise SourceArgumentNotFound(
            "street",
            street_name,
            "Could not extract street ID from response. The street name "
            "might be incorrect.",
        )
    return match.group(1)


def _ical_urls(source, street_id: str) -> list[str]:
    """One ICS download per calendar year the schedule can span."""
    city = source.params["city"]
    house_no = source.params["house_number"]
    now = datetime.now()
    return [
        f"{_BASE_URL}/{city}/download/ical/{street_id}/{house_no}/{year}"
        for year in (now.year, now.year + 1)
    ]


def _download_ical(source, url: str, street_id: str):
    """Fetch one year's calendar. The download is a POST, with no body."""
    r = source.session.post(url)
    r.raise_for_status()
    return r


@final
class Source(BaseSource):
    TITLE = "PreZero"
    DESCRIPTION = "Source for PreZero waste collection calendar"
    URL = _BASE_URL
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Bad Oeynhausen Aalstraße": {
            "street": "Aalstraße",
            "house_number": "1",
        },
        "Bad Oeynhausen Ackerstraße": {
            "street": "Ackerstraße",
            "house_number": "2",
        },
    }

    REGIONS = (
        region(
            "Bad Oeynhausen",
            url=f"{_BASE_URL}/bad-oeynhausen",
            city="bad-oeynhausen",
        ),
    )

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
        text_field("city", term=CITY, default="bad-oeynhausen"),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Geben Sie Ihre Straße und Hausnummer ein. Diese Quelle "
            "unterstützt derzeit nur Bad Oeynhausen."
        ),
        "en": (
            "Enter your street and house number. This source currently only "
            "supports Bad Oeynhausen."
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=_resolve_street_id,
        targets=_ical_urls,
        fetch=_download_ical,
    )
    parse = parsers.EachResponse(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Biotonne": ORGANIC,
            "Gelbe Tonne": RECYCLABLES,
            "Restmülltonne": GENERAL_WASTE,
            "Restmülltonne 4-wl.": GENERAL_WASTE,
            "Papiertonne": PAPER,
            "Schadstoffsammlung": HAZARDOUS,
        }
    )
