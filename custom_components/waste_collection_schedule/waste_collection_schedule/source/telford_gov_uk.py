import json
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, postcode, uprn
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API = "https://dac.telford.gov.uk/BinDayFinder/Find"

_TYPE_MAP = {
    "Red Top Container": wt.GENERAL_WASTE,
    "Purple / Blue Containers": wt.RECYCLABLES,
    "Green Container": wt.GARDEN_WASTE,
    "Silver Containers": wt.FOOD_WASTE,
}


def _pick_uprn(response, *keys, post_code=None, name_number=None, **_) -> str:
    """The postcode search answers a JSON document held inside a JSON string."""
    if response.status_code == 500:
        raise SourceArgumentException(
            "post_code",
            "Postcode is not in the correct format or service is unavailable",
        )
    response.raise_for_status()
    properties = json.loads(response.json())["properties"]
    if not properties:
        raise SourceArgumentNotFound("post_code", post_code)
    wanted = str(name_number).strip().lower()
    for prop in properties:
        if prop["PrimaryName"].lower() == wanted:
            return prop["UPRN"]
    raise SourceArgumentNotFoundWithSuggestions(
        "name_number", name_number, [prop["PrimaryName"] for prop in properties]
    )


def _decode(response, source=None) -> list:
    """The collection reply is a JSON string holding the JSON document."""
    return json.loads(response)["bincollections"]


def _date(record, source) -> str:
    """ "Wednesday 14th October" without its ordinal suffix."""
    return re.sub(r"(\d)(st|nd|rd|th)", r"\1", record["nextDate"])


@final
class Source(BaseSource):
    TITLE = "Telford and Wrekin Council"
    DESCRIPTION = "Source for telford.gov.uk, Telford and Wrekin Council, UK"
    URL = "https://www.telford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "10 Long Row Drive, Lawley": {"uprn": "000452097493"},
        "126 Dunsheath, Telford": {"post_code": "TF3 2DA", "name_number": "126"},
        "11 Pinewoods, Telford": {"post_code": "TF10 9LN", "name_number": "11"},
    }

    PARAMS = (
        alternatives(
            [uprn()],
            [postcode("post_code", "name_number")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter either your UPRN (available from "
            "[FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your "
            "postcode and the house name or number exactly as the council lists "
            "it (e.g. '126')."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/PostcodeSearch",
                params=lambda post_code=None, **_: {"postcode": post_code},
                given=lambda uprn=None, **_: uprn,
                pick=_pick_uprn,
                raise_for_status=False,
            ),
        ),
        url=f"{API}/PropertySearch",
        params=lambda key, **_: {"uprn": key},
    )

    parse = parsers.JsonParser()

    preprocess = Compose(
        _decode,
        ExplodeList(_date, into="date"),
    )

    transform = JsonTransformer(
        date_key="date",
        type_key="name",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.nearest_year("%A %d %B"),
    )
