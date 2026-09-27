from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, postcode, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://biffaleicester.co.uk/wp-admin/admin-ajax.php"


def _property_uprn(response, *, number, **_) -> str:
    """The UPRN of the postcode's address that starts with the house number."""
    addresses = response.json()["anyType"]
    for address in addresses:
        if address["UPRNAddress"].startswith(f"{number} "):
            return address["UPRNID"]
    raise SourceArgumentNotFoundWithSuggestions(
        "number", number, [address["UPRNAddress"] for address in addresses]
    )


@final
class Source(BaseSource):
    TITLE = "Leicester City Council"
    DESCRIPTION = "Source for city of Leicester, UK."
    URL = "https://www.leicester.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "30 Mayflower Rd, Leicester LE5 5QD": {"post_code": "LE5 5QD", "number": "30"},
        "235 Glenfield Rd, Leicester LE3 6DL": {"uprn": "002465020938"},
    }

    PARAMS = (alternatives([uprn()], [postcode("post_code", "number")]),)

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                _API_URL,
                method="POST",
                data=lambda post_code, **_: {
                    "action": "get_uprn_api",
                    "postcode": post_code,
                },
                given=lambda uprn=None, **_: uprn or None,
                pick=_property_uprn,
            ),
        ),
        url=_API_URL,
        method="POST",
        data=lambda property_uprn, **_: {
            "action": "get_details_api",
            "uprn": property_uprn,
        },
        raise_for_status=True,
    )
    parse = parsers.JsonParser("anyType")
    transform = JsonTransformer(
        date_key="ServiceDueDate",
        type_key="ServiceMode",
        parse_date=date_parsers.for_format("%d/%m/%y"),
        type_value_map={
            "DW": wt.GENERAL_WASTE,
            "RY": wt.RECYCLABLES,
            "GW": wt.GARDEN_WASTE,
        },
    )
