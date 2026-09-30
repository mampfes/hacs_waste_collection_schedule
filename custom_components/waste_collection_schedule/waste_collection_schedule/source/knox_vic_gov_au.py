import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import ExplodeList
from waste_collection_schedule.transformers import JsonTransformer

API = "https://www.knox.vic.gov.au/rubbish-collection"

_TYPE_MAP = {
    "green": wt.GARDEN_WASTE,
    "rubbish": wt.GENERAL_WASTE,
    "recycling": wt.RECYCLABLES,
}


def _pick_address_id(response, *keys, street_address, **_) -> str:
    """The autocomplete answers ``[{"value": id, "label": address}, ...]``; take the top hit."""
    hits = response.json()
    if not isinstance(hits, list) or not hits:
        raise SourceArgumentNotFound("street_address", street_address)
    return hits[0]["value"]


def _services(record, source) -> list[dict]:
    """One row per ``<type>_date`` field: ``"Next collection is <span>30 September 2026</span>"``."""
    rows = []
    for key, value in record.items():
        if key.endswith("_date") and value:
            date = re.sub(r"<[^>]+>|Next collection is", "", value).strip()
            rows.append({"type": key.removesuffix("_date"), "date": date})
    return rows


@final
class Source(BaseSource):
    TITLE = "Knox City Council"
    DESCRIPTION = "Source for Knox City Council rubbish collection."
    URL = "https://www.knox.vic.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Lorna Café": {
            "street_address": "1053 Burwood Highway, FERNTREE GULLY VIC 3156"
        },
        "Country Cob Bakery": {
            "street_address": "951 Mountain Highway, BORONIA VIC 3155"
        },
    }

    PARAMS = (street_address("street_address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address as it appears on "
            "[Find my bin days](https://www.knox.vic.gov.au/our-services/bins-rubbish-and-recycling/find-my-bin-days), "
            "e.g. '1053 Burwood Highway, FERNTREE GULLY VIC 3156'. The first "
            "match is used."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{API}/autocomplete/find",
                params=lambda street_address, **_: {"q": street_address},
                pick=_pick_address_id,
            ),
        ),
        url=f"{API}/find",
        params=lambda key, **_: {"address": key},
    )

    parse = parsers.JsonParser()

    preprocess = ExplodeList(_services)

    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.for_format("%d %B %Y"),
    )
