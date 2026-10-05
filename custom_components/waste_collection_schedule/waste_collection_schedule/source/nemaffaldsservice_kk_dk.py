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
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://nemaffaldsservice.kk.dk"
_ADDRESS_LOOKUP_URL = f"{_BASE_URL}/WasteHome/AddressByTerm/"
_CUSTOMER_LOOKUP_URL = f"{_BASE_URL}/WasteHome/SearchCustomerRelation"
_CALENDAR_URL = f"{_BASE_URL}/Calendar/GetICaldendar"

_TOKEN_RE = re.compile(
    r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"'
)


def _pick_address(response, address: str, **_) -> str:
    """The provider's own autocomplete label for the configured address."""
    labels = []
    for suggestion in response.json() or []:
        if not suggestion.get("fullAdress"):
            continue
        label = suggestion.get("label", "")
        labels.append(label)
        if label.lower() == address.lower():
            return label

    raise SourceArgumentNotFoundWithSuggestions("address", address, labels)


def _pick_token(response, *keys, address: str, **_) -> str:
    """The CSRF token the search POST has to carry, off the homepage."""
    token_match = _TOKEN_RE.search(response.text)
    if token_match is None:
        raise SourceArgumentNotFoundWithSuggestions("address", address, [])
    return token_match.group(1)


def _pick_customer_id(response, matched_address, token, *, address: str, **_) -> str:
    """The customer id the search redirected to, off the final URL."""
    customer_id = parse_qs(urlparse(str(response.url)).query).get("customerId")
    if not customer_id:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, [matched_address]
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
        "Østerbrogade 100": {"address": "Østerbrogade 100"},
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
        steps=(
            Lookup(
                _ADDRESS_LOOKUP_URL,
                params=lambda address, **_: {"term": address},
                pick=_pick_address,
            ),
            Lookup(_BASE_URL, pick=_pick_token),
            Lookup(
                _CUSTOMER_LOOKUP_URL,
                method="POST",
                data=lambda matched_address, token, **_: {
                    "SearchTerm": matched_address,
                    "__RequestVerificationToken": token,
                },
                pick=_pick_customer_id,
            ),
        ),
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
            "Metal": wt.METAL,
            "Plast": wt.PLASTIC,
            "Elektronik": wt.ELECTRONICS,
            "Farligt affald": wt.HAZARDOUS,
            "Tekstil": wt.TEXTILES,
            "Storskrald": wt.BULKY_WASTE,
            "Haveaffald": wt.GARDEN_WASTE,
        },
    )
