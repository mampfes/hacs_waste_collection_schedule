"""Nem Affaldsservice (Københavns Kommune), Denmark.

Demonstrates: a genuinely bespoke multi-step retrieve that does not fit any
existing retriever. Getting to the ICS feed needs, in order: an address
autocomplete GET (to validate/normalise the address and offer suggestions on
a mismatch), a plain GET of the homepage to scrape a CSRF
(``__RequestVerificationToken``) value out of the HTML, a POST that submits
the matched address together with that token and redirects to a URL carrying
the resolved ``customerId`` query parameter, and finally the calendar GET
itself. Four sequential requests with state threaded between each (a matched
address, then a token, then a redirect-derived id) is a shape
``TwoStepRetriever`` (exactly one lookup + one schedule request) does not
cover; this is expressed as a plain ``retrieve`` method instead.
"""

import re
from typing import ClassVar, final
from urllib.parse import parse_qs, urlparse

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    ELECTRONICS,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_BASE_URL = "https://nemaffaldsservice.kk.dk"
_ADDRESS_LOOKUP_URL = f"{_BASE_URL}/WasteHome/AddressByTerm/"
_CUSTOMER_LOOKUP_URL = f"{_BASE_URL}/WasteHome/SearchCustomerRelation"
_CALENDAR_URL = f"{_BASE_URL}/Calendar/GetICaldendar"

_TOKEN_RE = re.compile(
    r'name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"'
)


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

    PARAMS = (
        text_field(
            "address",
            "Address",
        ),
    )

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

    def retrieve(self, source):
        session = self.session
        address = self.params["address"]

        suggestions_r = session.get(_ADDRESS_LOOKUP_URL, params={"term": address})
        suggestions_r.raise_for_status()
        suggestions = suggestions_r.json() or []

        matched_address = None
        labels = []
        for suggestion in suggestions:
            if not suggestion.get("fullAdress"):
                continue
            label = suggestion.get("label", "")
            labels.append(label)
            if label.lower() == address.lower():
                matched_address = label
                break

        if matched_address is None:
            raise SourceArgumentNotFoundWithSuggestions("address", address, labels)

        home_r = session.get(_BASE_URL)
        home_r.raise_for_status()
        token_match = _TOKEN_RE.search(home_r.text)
        if token_match is None:
            raise SourceArgumentNotFoundWithSuggestions("address", address, [])
        token = token_match.group(1)

        search_r = session.post(
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
                "address", address, [matched_address]
            )

        r = session.get(_CALENDAR_URL, params={"customerId": customer_id[0]})
        r.raise_for_status()
        return r

    parse = parsers.IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "Restaffald": GENERAL_WASTE,
            "Madaffald": ORGANIC,
            "Bioposer": ORGANIC,
            "Papir": PAPER,
            "Pap": PAPER,
            "Glas": GLASS,
            "Metal": RECYCLABLES,
            "Plast": RECYCLABLES,
            "Elektronik": ELECTRONICS,
            "Farligt affald": HAZARDOUS,
            "Tekstil": RECYCLABLES,
            "Storskrald": BULKY_WASTE,
            "Haveaffald": GARDEN_WASTE,
        }
    )

    def __init__(self, address: str):
        super().__init__(address=address.strip())
