from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

# One record per container, each carrying its planned emptyings, each naming
# the fractions collected. A split bin empties two fractions of one type on
# the same day (metal and plastic).


@final
class Source(BaseSource):
    TITLE = "Renosyd"
    DESCRIPTION = "Renosyd collections for Skanderborg and Odder kommunes"
    URL = "https://renosyd.dk"
    COUNTRY = "dk"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.GLASS,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.TEXTILES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "TestCase1": {"house_number": "013000"},
        "TestCase2": {"house_number": "012000"},
        "TestCase3": {"house_number": 11000},
    }

    PARAMS = (text_field("house_number", "Standplads number"),)

    retrieve = HttpGetRetriever(
        url="https://skoda-selvbetjeningsapi.renosyd.dk/api/v1/toemmekalender",
        # The standplads number is six digits, zero-padded.
        params=lambda house_number, **_: {"nummer": str(house_number).zfill(6)},
    )
    parse = parsers.JsonParser()
    preprocess = Compose(
        ExplodeList("planlagtetømninger"),
        ExplodeList("fraktioner", into="fraktion"),
    )
    transform = JsonTransformer(
        date_key=lambda record: record["dato"][:10],
        type_key="fraktion",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Restaffald": wt.GENERAL_WASTE,
            "Madaffald": wt.FOOD_WASTE,
            "Glas": wt.GLASS,
            "Papir": wt.PAPER,
            "Pap": wt.PAPER,
            "Plast": wt.RECYCLABLES,
            "Metal": wt.RECYCLABLES,
            "Mad- og drikkekartoner": wt.RECYCLABLES,
            "Tekstilaffald": wt.TEXTILES,
        },
        carry_raw_label=True,
    )
