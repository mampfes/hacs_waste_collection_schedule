import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.preprocessors import Compose, DateFields, RowFilter
from waste_collection_schedule.transformers import ICSTransformer

_CHECKER_JS = (
    "https://www.eastriding.gov.uk/templates/eryc_corptranet/js/eryc-bin-checker.js"
)
_API_URL = (
    "https://wasterecyclingapi.eastriding.gov.uk/api/RecyclingData/CollectionsData"
)


def _credentials(response, **_) -> tuple[str, str]:
    """The API key and licensee the council's bin checker script embeds."""
    api_key = re.findall(r"APIKey=(.+)&L", response.text)[0]
    licensee = re.findall(r"Licensee=(.+)&", response.text)[0]
    return api_key, licensee


def _is_property(record, source) -> bool:
    """The postcode lists every property in it; keep the configured one."""
    return record["UPRN"] == str(source.params["uprn"]).zfill(12)


@final
class Source(BaseSource):
    TITLE = "East Riding of Yorkshire Council"
    DESCRIPTION = "Source for East Riding of Yorkshire Council, UK."
    URL = "https://eastriding.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "010002364380", "postcode": "DN14 6BJ"},
        "Test_002": {"uprn": "100050020969", "postcode": "YO16 4HF"},
        "Test_003": {"uprn": "100050099708", "postcode": "HU12 0PE"},
        "Test_004": {"uprn": 10002364380, "postcode": " DN146BJ "},
    }

    PARAMS = (uprn(), postcode())

    retrieve = retrievers.Request(
        _API_URL,
        params=lambda credentials, postcode, **_: {
            "APIKey": credentials[0],
            "Licensee": credentials[1],
            "Postcode": str(postcode).strip().replace(" ", ""),
        },
        # Without it the API answers XML.
        headers={"Accept": "application/json"},
        before=(retrievers.Lookup(_CHECKER_JS, pick=_credentials),),
    )
    parse = parsers.JsonParser("dataReturned")
    # The bins are named by colour only.
    preprocess = Compose(
        RowFilter(_is_property),
        DateFields(
            fields={
                "GreenDate": "Green Bin",
                "BlueDate": "Blue Bin",
                "BrownDate": "Brown Bin",
            },
            parse_date=lambda value: (
                date_parsers.for_format("%Y-%m-%d")(value[:10]) if value else None
            ),
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "Green Bin": wt.GENERAL_WASTE,
            "Blue Bin": wt.RECYCLABLES,
            "Brown Bin": wt.GARDEN_WASTE,
        }
    )
