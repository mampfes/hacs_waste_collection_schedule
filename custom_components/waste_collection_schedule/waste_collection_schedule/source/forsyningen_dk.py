"""Frederikshavn Forsyning (forsyningen.dk), Denmark.

The utility's "Min side" portal (a Renomatic installation) is public:

1. ``/minside/Adresse/Typeahead?query=<address>`` returns matching addresses
   as JSON, each with its ``AdresseId`` and the address as printed
   ("Knivholtvej 15 (9900)").
2. ``/minside/Tomningsinfo?siteType=R&adresseId=<id>`` renders the address's
   bins as a table, one row per bin ("240L Rumopdelt Mad/Rest Tømmes hver 2
   uge") with its next three collections as day-month dates ("26-10, 9-11,
   23-11").

The table carries no year, so each date is placed in the year nearest today
(the list is always the next few weeks). A bin emptied on demand ("Tømmes efter
behov") lists no dates and contributes nothing. The per-address PDF calendar
the portal also offers takes about 20 seconds to render and is not used.
"""

import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import RowTransformer

BASE_URL = "https://renovation.forsyningen.dk/minside"

# "240L Rumopdelt Mad/Rest Tømmes hver 2 uge" -> "Mad/Rest";
# "5M3 Plast/metal/karton Tømmes efter behov" -> "Plast/metal/karton".
_BIN = re.compile(
    r"^\s*[\d.,]+\s*(?:L|M3)\s+(?:Rumopdelt\s+)?(.*?)\s+Tømmes\b", re.IGNORECASE
)


def _address_id(response: Any, *_keys: Any, address: str, **_: Any) -> int:
    """The AdresseId of the suggestion spelled like the configured address.

    The configured address may leave out the postcode the portal appends in
    parentheses ("Knivholtvej 15" matches "Knivholtvej 15 (9900)").
    """
    wanted = lookups.normalize_loose(address)
    found = response.json() or []
    for item in found:
        printed = item.get("Beliggenhed", "")
        street_part = re.sub(r"\s*\(\d{4}\)\s*$", "", printed)
        if wanted in (
            lookups.normalize_loose(printed),
            lookups.normalize_loose(street_part),
        ):
            return item["AdresseId"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [item.get("Beliggenhed", "") for item in found]
    )


def _bin_label(label: str) -> str:
    match = _BIN.match(label)
    return match.group(1).strip() if match else label.strip()


@final
class Source(BaseSource):
    TITLE = "Frederikshavn Forsyning"
    DESCRIPTION = "Source for Frederikshavn Forsyning (Frederikshavn Kommune)."
    URL = "https://www.forsyningen.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Hjørringvej 10": {"address": "Hjørringvej 10"},
        "Knivholtvej 15 (9900)": {"address": "Knivholtvej 15 (9900)"},
    }

    PARAMS = (street_address(),)

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.PAPER,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as the address search on "
            "https://renovation.forsyningen.dk/minside/Tomningsinfo suggests it, "
            "e.g. 'Hjørringvej 10' or 'Knivholtvej 15, 1 (9900)'."
        ),
        "da": (
            "Indtast adressen, som adressesøgningen på "
            "https://renovation.forsyningen.dk/minside/Tomningsinfo foreslår den, "
            "f.eks. 'Hjørringvej 10' eller 'Knivholtvej 15, 1 (9900)'."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{BASE_URL}/Adresse/Typeahead",
                params=lambda address, **_: {"query": address, "limit": 10},
                pick=_address_id,
            ),
        ),
        url=f"{BASE_URL}/Tomningsinfo",
        params=lambda address_id, **_: {"siteType": "R", "adresseId": address_id},
    )
    parse = parsers.HtmlLabelledDates(
        "#table tbody tr",
        label="td:nth-of-type(1)",
        date="td:nth-of-type(4)",
        date_pattern=r"(\d{1,2}-\d{1,2})",
        all_dates=True,
    )
    transform = RowTransformer(
        parse_date=date_parsers.nearest_year("%d-%m"),
        clean=_bin_label,
        type_value_map={
            "Genbrug": wt.RECYCLABLES,
            "Mad/Rest": wt.GENERAL_WASTE,
            "Mad": wt.FOOD_WASTE,
            "Papir/Pap": wt.PAPER,
            "Plast/Metal/Kartoner": wt.RECYCLABLES,
            "Plast/metal/karton": wt.RECYCLABLES,
        },
        carry_raw_label=True,
    )
