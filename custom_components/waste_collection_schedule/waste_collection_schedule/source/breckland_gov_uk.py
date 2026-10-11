from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    street_address,
    uprn,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.service.JaduApiserver import rpc
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://www.breckland.gov.uk/apiserver/ajaxlibrary"
_HEADERS = {"referer": "https://www.breckland.gov.uk/mybreckland"}


def _site_uprn(response, *_, address, **__) -> str:
    """The UPRN of the last site at the postcode whose name contains ``address``."""
    sites = response.json()["result"]
    found = None
    for site in sites:
        if str(address).lower() in site["name"].lower():
            found = site["uprn"]
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, [site["name"] for site in sites]
        )
    return found


@final
class Source(BaseSource):
    TITLE = "Breckland Council"
    DESCRIPTION = "Source for breckland.gov.uk"
    URL = "https://www.breckland.gov.uk/mybreckland"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "test1": {"postcode": "IP22 2LJ", "address": "glen travis"},
        "test2": {"uprn": "10011977093"},
    }

    PARAMS = (alternatives([uprn()], [postcode(), street_address()]),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or your postcode plus part of your address as "
            "the council lists it. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    retrieve = rpc(
        _API_URL,
        "Breckland.Whitespace.JointWasteAPI.GetBinCollectionsByUprn",
        lambda site_uprn, **_: {"uprn": str(site_uprn), "environment": "live"},
        request_id="",
        headers=_HEADERS,
        before=(
            Lookup(
                rpc(
                    _API_URL,
                    "Breckland.Whitespace.JointWasteAPI.GetSiteIDsByPostcode",
                    lambda postcode, **_: {"postcode": postcode, "environment": "live"},
                    request_id="",
                    headers=_HEADERS,
                ),
                given=lambda uprn=None, **_: uprn,
                pick=_site_uprn,
            ),
        ),
    )
    parse = parsers.JsonParser("result")
    transform = JsonTransformer(
        date_key="nextcollection",
        type_key="collectiontype",
        parse_date=date_parsers.for_format("%d/%m/%Y %H:%M:%S"),
        type_value_map={
            "Refuse Collection Service": wt.GENERAL_WASTE,
            "Recycling Collection Service": wt.RECYCLABLES,
            "Garden Waste Service": wt.GARDEN_WASTE,
            "Food Waste Collection Service": wt.FOOD_WASTE,
        },
    )
