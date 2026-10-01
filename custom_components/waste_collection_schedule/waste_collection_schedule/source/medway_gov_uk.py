from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, postcode, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

API_BASE = "https://api.medway.gov.uk/api"
HEADERS = {
    "Origin": "https://www.medway.gov.uk",
    "Referer": "https://www.medway.gov.uk/",
}
LABEL = "Waste Collection"


def _pick_uprn(response, *keys, postcode, housenameornumber, **_) -> str:
    """The lookup answers a list of addresses; match the house name/number."""
    addresses = response.json()
    if not addresses:
        raise SourceArgumentNotFound("postcode", postcode)
    search = str(housenameornumber).strip().lower()
    for addr in addresses:
        if search in (
            (addr.get("paon") or "").lower(),
            (addr.get("saon") or "").lower(),
        ):
            return str(addr["uprn"])
    raise SourceArgumentNotFoundWithSuggestions(
        "housenameornumber",
        housenameornumber,
        [a["addressText"] for a in addresses],
    )


@final
class Source(BaseSource):
    TITLE = "Medway Council"
    DESCRIPTION = "Source for medway.gov.uk services for Medway Council"
    URL = "https://www.medway.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "known_uprn": {"uprn": "100062390963"},
        "known_uprn_as_number": {"uprn": 100062390963},
        "by_postcode": {"postcode": "ME4 4AY", "housenameornumber": "194-198"},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode("postcode", "housenameornumber")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by entering your postcode at "
            "https://www.medway.gov.uk/homepage/45/check_collection_day. "
            "Alternatively provide your postcode and house name/number exactly "
            "as shown on the Medway website (e.g. '194-198')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                lambda postcode=None, **_: (
                    f"{API_BASE}/addressing/getaddresses/"
                    f"{str(postcode).replace(' ', '').lower()}"
                ),
                headers=HEADERS,
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
            ),
        ),
        url=lambda key, **_: f"{API_BASE}/waste/getwasteday/{key}",
        headers=HEADERS,
    )

    parse = parsers.JsonParser()

    transform = JsonTransformer(
        date_key="nextCollection",
        type_key=lambda record: LABEL,
        type_value_map={LABEL: wt.GENERAL_WASTE},
        parse_date=date_parsers.auto,
    )
