from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    alternatives,
    postcode,
    street_address,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import ArgumentGuard, JsonParser
from waste_collection_schedule.preprocessors import Compose, ExplodeList, RowFilter
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import JsonTransformer

_BASE_URL = "https://www.bury.gov.uk/app-services"


def _normalise(address: str) -> str:
    return address.replace(",", "").replace(" ", "").upper()


def _property_id(response, *, postcode: str, address: str, **_) -> str:
    """The id of the property at the postcode whose first address line matches."""
    data = response.json()
    if data["error"]:
        raise SourceArgumentNotFound("postcode", postcode)
    properties = data["response"]
    for item in properties:
        if _normalise(item["addressLine1"]) == _normalise(address):
            return item["id"]
    raise SourceArgumentNotFoundWithSuggestions(
        "address", address, [item["addressLine1"] for item in properties]
    )


def _bins(record, source) -> list:
    """One record per bin colour, the colour written into the record."""
    return [{"colour": colour, **bin_} for colour, bin_ in record["bins"].items()]


@final
class Source(BaseSource):
    TITLE = "Bury Council"
    DESCRIPTION = "Source for bury.gov.uk services for Bury Council, UK."
    URL = "https://bury.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_Address_001": {"postcode": "bl81dd", "address": "2 Oakwood Close"},
        "Test_Address_002": {"postcode": "bl8 2sg", "address": "9, BIRKDALE DRIVE"},
        "Test_Address_003": {"postcode": "BL8 3DG", "address": "18, slaidburn drive"},
        "Test_ID_001": {"id": 649158},
        "Test_ID_002": {"id": "593456"},
    }

    PARAMS = (
        alternatives(
            [postcode(), street_address()],
            [text_field("id", "Property ID")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your postcode and the first line of your address as listed on "
            "https://bury.gov.uk. Alternatively enter the property id: it is the "
            "`id` of your address in the response of "
            "https://www.bury.gov.uk/app-services/getProperties?postcode=<postcode>."
        ),
    }

    # The property id is either given, or found by the postcode and address.
    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                f"{_BASE_URL}/getProperties",
                params=lambda postcode=None, **_: {"postcode": postcode},
                given=lambda id=None, **_: None if id is None else str(id).zfill(6),
                pick=_property_id,
            ),
        ),
        url=f"{_BASE_URL}/getPropertyById",
        params=lambda property_id, **_: {"id": property_id},
    )

    # An unknown id is answered with an error message and no "bins".
    parse = ArgumentGuard(
        JsonParser("response"),
        argument="id",
        contains='"bins":',
        hint="check the property id",
    )

    # A bin without a next collection (e.g. a service the property does not
    # have) carries no date.
    preprocess = Compose(
        ExplodeList(_bins),
        RowFilter(lambda record, source: record.get("nextCollection")),
    )

    transform = JsonTransformer(
        date_key="nextCollection",
        type_key="colour",
        type_value_map={
            "grey": wt.GENERAL_WASTE,
            "brown": wt.GARDEN_WASTE,
            "green": wt.PAPER,
            "blue": wt.RECYCLABLES,
        },
    )
