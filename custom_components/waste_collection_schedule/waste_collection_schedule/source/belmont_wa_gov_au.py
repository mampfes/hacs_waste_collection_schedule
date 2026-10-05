from typing import ClassVar, final
from urllib.parse import urlencode

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    DateFields,
    DefaultPreprocessor,
)
from waste_collection_schedule.transformers import ICSTransformer

_API = "https://www.belmont.wa.gov.au/api/intramaps"

_parse_date = date_parsers.for_format("%Y-%m-%dT%H:%M:%S")


def _pick_property(lookup, source) -> dict:
    """The one property the address search matched, as its map and db keys."""
    # An address nothing matches is answered with an empty body, not `[]`.
    matches = lookup.json() if lookup.text.strip() else []
    address = source.params["address"]
    if len(matches) == 0:
        raise SourceArgumentNotFound("address", address)
    if len(matches) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "address", address, [m.get("Address") for m in matches]
        )
    return {"mapkey": matches[0]["mapkey"], "dbkey": matches[0]["dbkey"]}


@final
class Source(BaseSource):
    TITLE = "Belmont City Council"
    DESCRIPTION = "Source for Belmont City Council rubbish collection."
    URL = "https://www.belmont.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "PETstock Belmont": {"address": "196 Abernethy Road Belmont 6104"},
        "Belgravia Medical Centre": {"address": "374 Belgravia Street Cloverdale 6105"},
        "IGA Rivervale": {"address": "126 Kooyong Road Rivervale 6103"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown address": {"address": "1 Nowhere Street Belmont 6104"},
    }

    PARAMS = (street_address(),)

    retrieve = retrievers.TwoStepRetriever(
        lookup_url=lambda address, **_: (
            f"{_API}/getaddresses?{urlencode({'key': address})}"
        ),
        extract=_pick_property,
        schedule_url=lambda key, **_: (
            f"{_API}/getpropertydetailswithlocalgov?{urlencode(key)}"
        ),
        # A browser's Accept header makes the API answer XML.
        headers={"Accept": "application/json"},
    )
    parse = parsers.JsonParser("data")
    # One record carries the next date of each stream in its own field.
    preprocess = Compose(
        DefaultPreprocessor(),
        DateFields(
            fields={
                "BinDayGeneralWasteFormatted": "General Waste",
                "BinDayRecyclingFormatted": "Recycling",
            },
            parse_date=lambda value: _parse_date(value) if value else None,
        ),
    )
    transform = ICSTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
        },
    )
