from typing import ClassVar, TypedDict, final

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
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import SplitByFields
from waste_collection_schedule.retrievers import TwoStepRetriever
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://api.bathnes.gov.uk/webapi/api/{}"
_LOOKUP_URL = _API_URL.format("AddressesAPI/v2/search/{postcode}/150/true")
_SCHEDULE_URL = _API_URL.format(
    "BinsAPI/v2/BartecFeaturesandSchedules/CollectionSummary/{uprn}"
)


class _Address(TypedDict):
    payment_Address: str
    uprn: int | float | str


class _Entry(TypedDict):
    featureType: str
    previousCollectionDate: str
    nextCollectionDate: str


def _extract_uprn(lookup, source) -> int:
    addresses: list[_Address] = JsonParser(shape=list[_Address])(lookup, source)
    if not addresses:
        raise SourceArgumentNotFound("postcode", source.params["postcode"])

    housenameornumber = str(source.params["housenameornumber"])
    suggestions: list[str] = []
    for address in addresses:
        candidate = _address_housenameornumber(address)
        if not candidate:
            continue
        if candidate.casefold() == housenameornumber.casefold():
            return int(address["uprn"])
        suggestions.append(candidate)

    raise SourceArgumentNotFoundWithSuggestions(
        "housenameornumber", housenameornumber, suggestions
    )


def _address_housenameornumber(address: _Address) -> str | None:
    parts = address["payment_Address"].split("|")
    if len(parts) < 2:
        return None
    return str(parts[1].strip())


@final
class Source(BaseSource):
    TITLE = "Bath & North East Somerset Council"
    DESCRIPTION = (
        "Source for bathnes.gov.uk services for Bath & North East Somerset Council"
    )
    URL = "https://bathnes.gov.uk"
    COUNTRY = "uk"

    TEST_CASES: ClassVar[dict] = {
        "uprn": {"uprn": "10001138699"},
        "houseNumber": {"postcode": "BA1 2LR", "housenameornumber": 1},
        "houseName": {
            "postcode": "BA1 5SX",
            "housenameornumber": "St Stephen's Church",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide your UPRN, or both your postcode and house name "
            "or number. Find your UPRN at https://www.findmyaddress.co.uk/"
        ),
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [
                postcode(),
                text_field("housenameornumber", label="House Name or Number"),
            ],
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    RAISE_ON_EMPTY = True

    retrieve = TwoStepRetriever(
        lookup_url=lambda postcode, **_: _LOOKUP_URL.format(postcode=postcode),
        extract=_extract_uprn,
        schedule_url=lambda found_uprn, **_: _SCHEDULE_URL.format(uprn=int(found_uprn)),
        direct_key=lambda source: source.params.get("uprn"),
    )
    parse = JsonParser(shape=list[_Entry])
    preprocess = SplitByFields(
        src_keys=("previousCollectionDate", "nextCollectionDate"), dst_key="date"
    )
    transform = JsonTransformer(
        date_key="date",
        type_key="featureType",
        type_value_map={
            "Residual": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
        },
    )
