"""PreZero waste collection calendar network (abfallkalender.prezero.network).

Demonstrates: a redirect-driven street lookup (a POST that 302s to a URL
carrying the resolved street id, with an HTML meta-refresh fallback for
deployments that redirect that way instead) feeding two fixed-year ICS
downloads. No configured retriever expresses "POST, read the id out of the
redirect target rather than the response body, then always fetch two ICS
years", hence a source-defined retrieve()/parse() pair.
"""

import re
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import IcsParser
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


def _resolve_street_id(session, city: str, street_name: str, house_no: str) -> str:
    base_url = f"{_BASE_URL}/{city}"
    r = session.post(
        base_url,
        data={"street": street_name, "houseNo": house_no},
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
        "Willich Aachener Straße": {
            "city": "willich",
            "street": "Aachener Straße",
            "house_number": "1",
        },
        "Willich Ahornweg": {
            "city": "willich",
            "street": "Ahornweg",
            "house_number": "5",
        },
    }

    REGIONS = (
        region(
            "Bad Oeynhausen",
            url=f"{_BASE_URL}/bad-oeynhausen",
            city="bad-oeynhausen",
        ),
        region("Willich", url=f"{_BASE_URL}/willich", city="willich"),
    )

    PARAMS = (
        street(field="street"),
        house_number(field="house_number"),
        text_field(
            "city",
            "City",
            default="bad-oeynhausen",
        ),
    )

    HOWTO: ClassVar[dict] = {
        "de": (
            "Geben Sie Ihre Straße und Hausnummer ein. Die Stadt ist "
            "standardmäßig auf Bad Oeynhausen eingestellt (unterstützt: Bad "
            "Oeynhausen, Willich)."
        ),
        "en": (
            "Enter your street and house number. The city defaults to Bad "
            "Oeynhausen (supported: Bad Oeynhausen, Willich)."
        ),
    }

    def retrieve(self, source):
        session = source.session
        city = self.params["city"]
        street_name = self.params["street"]
        house_no = self.params["house_number"]

        street_id = _resolve_street_id(session, city, street_name, house_no)

        now = datetime.now()
        responses = []
        for year in (now.year, now.year + 1):
            ical_url = f"{_BASE_URL}/{city}/download/ical/{street_id}/{house_no}/{year}"
            r = session.post(ical_url)
            r.raise_for_status()
            responses.append(r)
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

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

    def __init__(self, street: str, house_number: str, city: str = "bad-oeynhausen"):
        super().__init__(street=street, house_number=house_number, city=city)
