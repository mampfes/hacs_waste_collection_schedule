"""Nem Affaldsservice (Københavns Kommune), Denmark.

Composes: :class:`~waste_collection_schedule.retrievers.LookupChainRetriever`.
Getting to the ICS feed needs, in order: an address autocomplete GET (to
validate/normalise the address and offer suggestions on a mismatch), a plain
GET of the homepage to scrape a CSRF (``__RequestVerificationToken``) value out
of the HTML, a POST that submits the matched address together with that token
and is redirected to a URL carrying the resolved ``customerId``, and finally
the calendar GET itself. That is three lookups then the schedule request, which
is exactly what a lookup chain is for: each level's answer is the next level's
input, so they cannot be issued in parallel or folded into one.

The third step reads its id off the *final* URL after the redirect. That only
replays because the cassette records it; it did not before, which is what made
this source look unreplayable (#7046).
"""

import re
from typing import ClassVar, final
from urllib.parse import parse_qs, urlparse

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://nemaffaldsservice.kk.dk"
_ADDRESS_LOOKUP_URL = f"{_BASE_URL}/WasteHome/AddressByTerm/"
_CUSTOMER_LOOKUP_URL = f"{_BASE_URL}/WasteHome/SearchCustomerRelation"
_CALENDAR_URL = f"{_BASE_URL}/Calendar/GetICaldendar"

_TOKEN_RE = re.compile(
    r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"'
)


def _resolve_address(source, keys: tuple) -> str:
    """Validate the address against the provider's own autocomplete."""
    address = source.params["address"]
    suggestions_r = source.session.get(_ADDRESS_LOOKUP_URL, params={"term": address})
    suggestions_r.raise_for_status()

    labels = []
    for suggestion in suggestions_r.json() or []:
        if not suggestion.get("fullAdress"):
            continue
        label = suggestion.get("label", "")
        labels.append(label)
        if label.lower() == address.lower():
            return label

    raise SourceArgumentNotFoundWithSuggestions("address", address, labels)


def _resolve_token(source, keys: tuple) -> str:
    """Scrape the CSRF token the search POST has to carry."""
    home_r = source.session.get(_BASE_URL)
    home_r.raise_for_status()
    token_match = _TOKEN_RE.search(home_r.text)
    if token_match is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", source.params["address"], []
        )
    return token_match.group(1)


def _resolve_customer_id(source, keys: tuple) -> str:
    """POST the search; the redirect's query string carries the customer id."""
    matched_address, token = keys
    search_r = source.session.post(
        _CUSTOMER_LOOKUP_URL,
        data={
            "SearchTerm": matched_address,
            "__RequestVerificationToken": token,
        },
    )
    search_r.raise_for_status()

    customer_id = parse_qs(urlparse(str(search_r.url)).query).get("customerId")
    if not customer_id:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", source.params["address"], [matched_address]
        )
    return customer_id[0]


@final
class Source(BaseSource):
    TITLE = "Nem Affaldsservice (Københavns Kommune)"
    DESCRIPTION = (
        "Source for Nem Affaldsservice, the waste collection schedule service "
        "of Københavns Kommune (City of Copenhagen), Denmark."
    )
    URL = _BASE_URL
    COUNTRY = "dk"

    TEST_CASES: ClassVar[dict] = {
        "Nørrebrogade 10": {"address": "Nørrebrogade 10"},
        "Amagerbrogade 10": {"address": "Amagerbrogade 10"},
        "Rådhuspladsen 1": {"address": "Rådhuspladsen 1"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as it appears in Denmark, e.g. "
            "'Nørrebrogade 10'. You can verify the spelling by typing your street "
            "and house number into the search box on "
            "https://nemaffaldsservice.kk.dk/ - if the site offers your address "
            "as an autocomplete suggestion, that exact text is what should be "
            "used here. If the address cannot be found, the resulting error "
            "message will list similar addresses to help you find the correct "
            "spelling."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(_resolve_address, _resolve_token, _resolve_customer_id),
        url=_CALENDAR_URL,
        params=lambda *keys, **_: {"customerId": keys[-1]},
    )

    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restaffald": wt.GENERAL_WASTE,
            "Madaffald": wt.ORGANIC,
            "Bioposer": wt.ORGANIC,
            "Papir": wt.PAPER,
            "Pap": wt.PAPER,
            "Glas": wt.GLASS,
            "Metal": wt.RECYCLABLES,
            "Plast": wt.RECYCLABLES,
            "Elektronik": wt.ELECTRONICS,
            "Farligt affald": wt.HAZARDOUS,
            "Tekstil": wt.RECYCLABLES,
            "Storskrald": wt.BULKY_WASTE,
            "Haveaffald": wt.GARDEN_WASTE,
        }
    )
