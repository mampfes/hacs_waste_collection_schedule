from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import Lookup
from waste_collection_schedule.service.JaduApiserver import rpc
from waste_collection_schedule.transformers import JsonTransformer

_API_URL = "https://www.southtyneside.gov.uk/apiserver/ajaxlibrary"
_HEADERS = {
    "Referer": "https://www.southtyneside.gov.uk/article/1023/Bin-collection-dates",
}


def _address_code(response, *_, uprn, **__) -> str:
    """``UPRN|Address`` for the property, the form the dates call asks for.

    The council prefixes some UPRNs with an ``S``, which users do not have.
    """
    for item in response.json()["result"]["ReturnedList"]:
        if str(uprn).strip() == item["UPRN"].lstrip("S"):
            return f"{item['UPRN']}|{item['Address']}"
    raise SourceArgumentNotFound("uprn", uprn)


@final
class Source(BaseSource):
    TITLE = "South Tyneside Council"
    DESCRIPTION = (
        "Source for southtyneside.gov.uk services for South Tyneside Council, UK."
    )
    URL = "https://southtyneside.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "NE34 8RY", "uprn": "100000342955"},
        "Test_002": {"postcode": "SR6 7AJ", "uprn": "100000359535"},
        "Test_003": {"postcode": "NE31 1LY", "uprn": 100000304486},
        "Test_004": {"postcode": "NE35 9BP", "uprn": 103009511},
    }

    PARAMS = (postcode(), uprn())

    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/.",
    }

    retrieve = rpc(
        _API_URL,
        "stc.waste.collections.getDates",
        lambda address_code, **_: {"addresscode": address_code},
        headers=_HEADERS,
        before=(
            Lookup(
                rpc(
                    _API_URL,
                    "stc.common.snippets.getAddressList",
                    lambda postcode, **_: {
                        "localonly": "true",
                        "postcode": str(postcode).replace(" ", ""),
                    },
                    headers=_HEADERS,
                ),
                pick=_address_code,
            ),
        ),
    )
    parse = parsers.JsonParser("result", "SortedCollections")
    preprocess = preprocessors.ExplodeList("Collections")
    transform = JsonTransformer(
        date_key="DateofCollection",
        type_key="TypeClass",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "HOUSEHOLD": wt.GENERAL_WASTE,
            "RECYCLING": wt.RECYCLABLES,
            "GARDEN": wt.GARDEN_WASTE,
        },
    )
