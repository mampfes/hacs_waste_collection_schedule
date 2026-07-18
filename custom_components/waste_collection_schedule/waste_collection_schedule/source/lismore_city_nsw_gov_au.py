import re
from typing import final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.field_terms import ADDRESS
from waste_collection_schedule.service.WhatBinDay import (
    TYPE_VALUE_MAP,
    WhatBinDayParser,
    WhatBinDayRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

TITLE = "Lismore City Council"
DESCRIPTION = (
    "Source for Lismore City Council waste collection services in NSW, Australia."
)
URL = "https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1"
COUNTRY = "au"

HOWTO = {
    "en": (
        "Enter the full service address used by Lismore City Council, for "
        "example '1 Rosella Chase, Goonellabah NSW 2480'."
    )
}

TEST_CASES = {
    "1 Rosella Chase, Goonellabah NSW 2480": {
        "address": "1 Rosella Chase, Goonellabah NSW 2480"
    },
    "10 Sibley St, NIMBIN NSW 2480": {"address": "10 Sibley St, NIMBIN NSW 2480"},
}

_ADDRESS_RE = re.compile(
    r"^(?:(?P<subpremise>(?:[A-Za-z]+\s+)?\d+[A-Za-z]?)\/)?"
    r"(?P<street_number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+"
    r"(?P<route>.+?)\s*,?\s+"
    r"(?P<locality>[A-Za-z ]+?)\s+"
    r"(?P<state>NSW|VIC|QLD|SA|WA|TAS|ACT|NT)\s+"
    r"(?P<postal_code>\d{4})$",
    flags=re.IGNORECASE,
)


def _split_address(address: str) -> dict:
    """Split a full free-text service address into WhatBinDay's parts.

    Lismore (unlike Kingston) takes a single address string, so this does the
    same-shape regex split the legacy Source._split_address did, just
    returning WhatBinDayRetriever's generic part names (street_name/suburb
    rather than route/locality) so the shared retriever can stay
    provider-agnostic.
    """
    normalized = " ".join(address.replace(",", " , ").split())
    match = _ADDRESS_RE.match(normalized)
    if not match:
        raise SourceArgumentNotFound("address", address)

    subpremise = (match.group("subpremise") or "").strip()
    street_number = match.group("street_number").strip()
    route = match.group("route").replace(" , ", " ").strip()
    locality = match.group("locality").strip().upper()
    state = match.group("state").strip().upper()
    postal_code = match.group("postal_code").strip()

    street_number_out = f"{subpremise}/{street_number}" if subpremise else street_number

    return {
        "street_number": street_number_out,
        "street_name": route,
        "suburb": locality,
        "post_code": postal_code,
        "state": state,
    }


@final
class Source(BaseSource):
    TITLE = TITLE
    DESCRIPTION = DESCRIPTION
    URL = URL
    COUNTRY = COUNTRY
    HOWTO = HOWTO

    TEST_CASES = TEST_CASES

    # An address-lookup source: an empty result means the address didn't
    # resolve, so surface a clear error rather than a silently-empty calendar.
    RAISE_ON_EMPTY = True

    PARAMS = (text_field("address", term=ADDRESS),)

    # Lismore only ever submits the parsed address text (no geocoding, unlike
    # Kingston): this matches the legacy source, which never passed
    # coordinates and so always fell back to WhatBinDay's default (Victorian)
    # coordinates. The device key is not address-specific for this provider
    # (a single static key is shared across every Lismore address), matching
    # the legacy service's fixed "lismore_city_council" location_key.
    retrieve = WhatBinDayRetriever(
        location_key="lismore_city_council",
        split_address=_split_address,
        address_field="address",
    )
    parse = WhatBinDayParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
