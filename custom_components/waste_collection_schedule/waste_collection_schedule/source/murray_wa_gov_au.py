from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API = "https://www.murray.wa.gov.au/api/cms/v1/wastecollection"
# The API answers XML unless JSON is asked for.
_HEADERS = {"Accept": "application/json"}


def _pick_guid(response, address: str, **_: Any) -> str:
    addresses = response.json()
    if not addresses:
        raise SourceArgumentNotFoundWithSuggestions("address", address, [])
    if len(addresses) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", address, [a["Address"] for a in addresses]
        )
    return addresses[0]["Guid"]


@final
class Source(BaseSource):
    TITLE = "Shire of Murray"
    DESCRIPTION = "Source for Shire of Murray waste collection."
    URL = "https://www.murray.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Visit https://www.murray.wa.gov.au/waste-and-environment/waste-and-recycling/bins.aspx and search for your address to verify it is found.",
    }

    TEST_CASES: ClassVar[dict] = {
        "41 Wilson Road, Pinjarra": {"address": "41 Wilson Road"},
        "58 McLarty Street, Dwellingup": {"address": "58 McLarty Street"},
        "28 Woodview Way, Barragup": {"address": "28 Woodview Way"},
    }

    PARAMS = (street_address(),)

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API}/GetAddressesByQuery",
                params=lambda address, **_: {"addressQuery": address.strip()},
                headers=_HEADERS,
                pick=_pick_guid,
            ),
        ),
        url=f"{_API}/GetAddressDetailsByGuid",
        params=lambda guid, **_: {"id": guid},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = parsers.JsonParser("CollectionData")
    transform = JsonTransformer(
        date_key="NextCollectionDate",
        type_key=lambda record: record["BinType"]["Name"],
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Verge Collection - Green waste": wt.GARDEN_WASTE,
            "Verge Collection - Hard waste": wt.BULKY_WASTE,
        },
    )
