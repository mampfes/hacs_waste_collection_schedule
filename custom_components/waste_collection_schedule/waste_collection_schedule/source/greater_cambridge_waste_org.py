import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
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
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import HtmlTransformer

API = "https://www.greatercambridgewaste.org/bin-calendar"

# The address list is an HTML fragment: one link per address, carrying the
# address text and its UPRN.
_ADDRESS = re.compile(
    r'data-address\s*=\s*"([^"]+)"\s*.*?data-id\s*=\s*"([^"]+)"',
    re.IGNORECASE | re.DOTALL,
)


def _pick_uprn(response, *keys, postcode, name_or_number, **_) -> str:
    if response.status_code == 400:
        raise SourceArgumentNotFound("postcode", postcode)
    response.raise_for_status()
    addresses = _ADDRESS.findall(response.json()["addresses"])
    wanted = str(name_or_number).strip().upper()
    for address, uprn_value in addresses:
        if wanted in address.upper():
            return uprn_value.strip()
    raise SourceArgumentNotFoundWithSuggestions(
        "name_or_number", wanted, [address for address, _ in addresses]
    )


@final
class Source(BaseSource):
    TITLE = "Greater Cambridge Waste, UK"
    DESCRIPTION = (
        "Source for greatercambridgewaste.org, the shared recycling and waste "
        "service for Cambridge City Council and South Cambridgeshire District Council."
    )
    URL = "https://greatercambridgewaste.org"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    REGIONS = (
        region("Cambridge City Council", url="https://cambridge.gov.uk/"),
        region("South Cambridgeshire District Council", url="https://scambs.gov.uk/"),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Cambs_uprn": {"uprn": 200004170895},
        "Cambs_houseNumber": {"postcode": "CB13JD", "name_or_number": 37},
        "Cambs_houseName": {"postcode": "cb215hd", "name_or_number": "ROSEMARY HOUSE"},
        "SCambs_uprn": {"uprn": 10091624540},
        "SCambs_houseNumber": {"postcode": "CB236GZ", "name_or_number": 53},
        "SCambs_houseName": {
            "postcode": "CB225HT",
            "name_or_number": "Rectory Farm Cottage",
        },
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode(), text_field("name_or_number", label="House Name or Number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode together with your house name "
            "or number. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/addresses",
                params=lambda postcode=None, **_: {
                    "postcode": str(postcode).strip().replace(" ", "").upper()
                },
                given=lambda uprn=None, **_: uprn,
                raise_for_status=False,
                pick=_pick_uprn,
            ),
        ),
        url=f"{API}/collections",
        params=lambda key, **_: {"uprn": key, "numberOfCollections": "12"},
        raise_for_status=True,
    )

    # The calendar is an HTML table inside the JSON reply; each collection is a
    # span labelled "Blue bin collection on Wednesday 30 September 2026".
    parse = parsers.HtmlParser("[aria-label]", from_json_key="tableRows")

    transform = HtmlTransformer(
        date_getter=lambda el: el["aria-label"].split(" collection on ")[1],
        type_getter=lambda el: el["aria-label"].split(" collection on ")[0],
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "Black bin": wt.GENERAL_WASTE,
            "Blue bin": wt.RECYCLABLES,
            "Green bin": wt.GARDEN_WASTE,
            "Food caddy": wt.FOOD_WASTE,
        },
    )
