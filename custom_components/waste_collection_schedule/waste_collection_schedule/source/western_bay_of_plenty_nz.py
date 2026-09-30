import json
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://kerbsidecollective.co.nz/wp-json/wbop/v1"
_HEADERS = {
    "Referer": "https://kerbsidecollective.co.nz/",
    "Origin": "https://kerbsidecollective.co.nz",
}


def _pick_valuation_id(response: Any, *_: Any, address: str, **__: Any) -> str:
    """The ValuationId of the first address the SOAP search answer lists."""
    match = re.search(r"<ValuationId>([^<]+)</ValuationId>", response.text)
    if match is None:
        raise SourceArgumentNotFound(
            "address",
            address,
            "make sure it matches an address in the Western Bay of Plenty district",
        )
    return match.group(1)


class _BinsParser(Parser["list[dict[str, Any]]"]):
    """The bins of the JSON object that follows the SOAP envelope in the reply."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[dict[str, Any]]":
        text = response.text
        start = text.find("{")
        if start < 0:
            raise ValueError("No JSON payload found in addressInfo2 response")
        result = (
            json.loads(text[start:])
            .get("GetRefuseInformationByValuationResponse", {})
            .get("GetRefuseInformationByValuationResult", {})
        )
        if result.get("ValuationFound") != "true":
            raise SourceArgumentNotFound(
                "address",
                source.params.get("address", "") if source else "",
                "no waste collection data found for this address",
            )
        connection = result.get("ServiceConnectionList", {}).get(
            "ServiceConnection", {}
        )
        bins = connection.get("BinInfo", {}).get("Bin", [])
        # A single bin comes back as an object rather than a list.
        if isinstance(bins, dict):
            bins = [bins]
        return [b for b in bins if b.get("NextPickupDate")]


@final
class Source(BaseSource):
    TITLE = "Western Bay of Plenty District Council"
    DESCRIPTION = "Source script for Western Bay of Plenty District Council kerbside collections via kerbsidecollective.co.nz"
    URL = "https://kerbsidecollective.co.nz/"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "15 Seaview Road": {"address": "15 Seaview Road"},
        "50 Ocean View Road": {"address": "50 Ocean View Road"},
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address as it appears on kerbsidecollective.co.nz, "
            "e.g. '15 Seaview Road'."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_API_URL}/addressSearch2",
                method="POST",
                data=lambda address, **_: {"term": address.strip()},
                headers=_HEADERS,
                pick=_pick_valuation_id,
            ),
        ),
        url=f"{_API_URL}/addressInfo2",
        method="POST",
        data=lambda valuation_id, **_: {"term": valuation_id},
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = _BinsParser()
    transform = JsonTransformer(
        date_key="NextPickupDate",
        type_key="BinType",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "Rubbish": wt.GENERAL_WASTE,
            "Mixed Recycling": wt.RECYCLABLES,
            "Glass": wt.GLASS,
            "Food": wt.FOOD_WASTE,
            "Garden": wt.GARDEN_WASTE,
        },
    )
