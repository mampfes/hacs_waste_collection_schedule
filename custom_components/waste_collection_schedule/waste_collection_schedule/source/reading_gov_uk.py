from dataclasses import replace
from typing import TypedDict, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, text_field, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
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

# Demonstrates: alternative-input PARAMS (UPRN OR postcode + house) on the new
# BaseSource architecture, with a two-mode retrieve() method.
#
# The API embeds the UPRN in the collections URL path. A user may supply the
# UPRN directly, or supply a postcode + house name/number which the source
# resolves to a UPRN via the getaddresses lookup before fetching collections.
#
# Because either input group satisfies the source, every param is marked
# required=False and the cross-field check lives in __init__ (see
# stirling_wa_gov_au.py for the same pattern). parsers.JsonParser("collections")
# drills into the nested array for both modes.

_PARAMS_UPRN = replace(uprn(), required=False)
_PARAMS_POSTCODE = replace(postcode(), required=False)
_PARAMS_HOUSE = replace(
    text_field("housenameornumber", label="House Name or Number"), required=False
)

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

    TEST_CASES = {
        "known_uprn": {"uprn": "310027679"},
        "known_uprn as number": {"uprn": 310027679},
        "unknown_uprn_by_number": {"postcode": "RG31 5PN", "housenameornumber": "65"},
        "unknown_uprn_by_number as number": {
            "postcode": "RG31 5PN",
            "housenameornumber": 65,
        },
    }

    # TODO(arch): once the framework supports mutually-exclusive PARAMS groups,
    # this becomes a single uprn-or-address group. For now, listing each param
    # required=False with the cross-field check in __init__ is the prototype.
    PARAMS = [_PARAMS_UPRN, _PARAMS_POSTCODE, _PARAMS_HOUSE]

    HOWTO = {
        "en": (
            "Provide your UPRN, or provide both your postcode and house name "
            "or number. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    _TYPE_MAP = {
        "Domestic Waste Collection Service": GENERAL_WASTE,
        "Recycling Collection Service": RECYCLABLES,
        "Food Waste Collection Service": FOOD_WASTE,
        "Garden Waste Collection Service": GARDEN_WASTE,
    }

    parse = parsers.JsonParser("collections", shape=list[_Collection])

    transformer = JsonTransformer(
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
        super().__init__(
            uprn=uprn, postcode=postcode, housenameornumber=housenameornumber
        )
        if not any((uprn, postcode and housenameornumber)):
            errors = []
            if postcode:
                errors.append("housenameornumber")
            elif housenameornumber:
                errors.append("postcode")
            else:
                errors = ["uprn", "postcode", "housenameornumber"]
            raise SourceArgumentExceptionMultiple(
                errors,
                "Must provide either a UPRN or both the Postcode and House Name or Number",
            )
