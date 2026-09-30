import json
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.preprocessors import (
    Compose,
    ExplodeList,
    SelectExactMatch,
)
from waste_collection_schedule.transformers import JsonTransformer

URL = "https://www.toogoodtowaste.co.nz/"

_TYPE_MAP = {
    "red": wt.GENERAL_WASTE,
    "yellow": wt.RECYCLABLES,
    "blue": wt.GLASS,
    "green": wt.GARDEN_WASTE,
}


def _bins(record, source) -> list[str]:
    """``bin_list`` is a JSON-encoded string: ``'["red", "yellow"]'``."""
    return json.loads(record["attributes"]["bin_list"])


@final
class Source(BaseSource):
    TITLE = "Hutt City Council"
    DESCRIPTION = "Source for Hutt City Council."
    URL = URL
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Bus Barns": {"address": "493 Muritai Road EASTBOURNE"},  # Monday
        "Council": {"address": "30 Laings Road HUTT CENTRAL"},  # Tuesday
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your address exactly as the address finder on "
            "[toogoodtowaste.co.nz](https://www.toogoodtowaste.co.nz/) shows it, "
            "e.g. '30 Laings Road HUTT CENTRAL' (street in title case, suburb "
            "in capitals)."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(
        url=f"{URL}_designs/integrations/address-finder/addressdata.json",
        params=lambda address, **_: {"query": address},
    )

    parse = parsers.JsonParser()

    preprocess = Compose(
        SelectExactMatch(
            argument="address", key=lambda record: record["attributes"]["address"]
        ),
        ExplodeList(_bins, into="bin"),
    )

    transform = JsonTransformer(
        date_key=lambda record: record["attributes"]["next_collection_date"],
        type_key="bin",
        type_value_map=_TYPE_MAP,
    )
