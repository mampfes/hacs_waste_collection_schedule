from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    text_field,
    uprn,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Demonstrates: alternative-input PARAMS via config_params.alternatives() —
# the user provides a UPRN, OR a postcode + house name/number. validate()
# enforces exactly one group; no per-source cross-field check needed.
#
# The API embeds the UPRN in the collections URL path. A postcode + house is
# resolved to a UPRN via the getaddresses lookup (TwoStepRetriever) before
# fetching collections.

SEARCH_URLS = {
    "UPRN": "https://api.reading.gov.uk/rbc/getaddresses",
    "COLLECTION": "https://api.reading.gov.uk/api/collections",
}


class _Collection(TypedDict):
    """The fields the transformer reads from each collections entry."""

    date: str
    service: str


def _extract_nameornum(address: dict) -> str:
    nameornum, _ = address["SiteShortAddress"].split(f", {address['SiteAddress2']}, ")
    return nameornum


def _pick_uprn(lookup, source) -> str:
    """TwoStepRetriever extractor: postcode lookup response -> UPRN."""
    addresses = lookup.json()["Addresses"]
    if addresses is None:
        raise SourceArgumentNotFound("postcode", source.params.get("postcode"))
    wanted = str(source.params.get("housenameornumber"))
    address = next((a for a in addresses if _extract_nameornum(a) == wanted), None)
    if address is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "housenameornumber", wanted, {_extract_nameornum(a) for a in addresses}
        )
    return address["AccountSiteUprn"]


@final
class Source(BaseSource):
    TITLE = "Reading Council"
    DESCRIPTION = "Source for reading.gov.uk services for Reading Council."
    URL = "https://reading.gov.uk"
    COUNTRY = "uk"

    # The direct-UPRN path skips the postcode/house-number validation, so a
    # well-formed but wrong UPRN returns no collections. Surface that as an
    # error instead of a silently empty calendar (#6943).
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "known_uprn": {"uprn": "310027679"},
        "known_uprn as number": {"uprn": 310027679},
        "unknown_uprn_by_number": {"postcode": "RG31 5PN", "housenameornumber": "65"},
        "unknown_uprn_by_number as number": {
            "postcode": "RG31 5PN",
            "housenameornumber": 65,
        },
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode(), text_field("housenameornumber", label="House Name or Number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or provide both your postcode and house name "
            "or number. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    _TYPE_MAP: ClassVar[dict] = {
        "Domestic Waste Collection Service": GENERAL_WASTE,
        "Recycling Collection Service": RECYCLABLES,
        "Food Waste Collection Service": FOOD_WASTE,
        "Garden Waste Collection Service": GARDEN_WASTE,
    }

    parse = parsers.JsonParser("collections", shape=list[_Collection])

    transform = JsonTransformer(
        date_key="date",
        type_key="service",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map=_TYPE_MAP,
    )

    # Two-step: a UPRN fetches collections directly; otherwise resolve it from
    # the postcode lookup (picking the address by house name/number) first.
    retrieve = retrievers.TwoStepRetriever(
        lookup_url=lambda postcode=None, **_: f"{SEARCH_URLS['UPRN']}/{postcode}",
        extract=_pick_uprn,
        schedule_url=lambda key, **_: f"{SEARCH_URLS['COLLECTION']}/{key}",
        direct_key=lambda source: source.params.get("uprn"),
    )

    def __init__(self, uprn=None, postcode=None, housenameornumber=None):
        # validate() enforces the UPRN-or-(postcode+house) alternative via PARAMS.
        super().__init__(
            uprn=uprn, postcode=postcode, housenameornumber=housenameornumber
        )
