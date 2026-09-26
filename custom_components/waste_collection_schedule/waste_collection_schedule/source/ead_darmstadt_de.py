from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.preprocessors import FlattenGroups
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

# The reply maps each date to the rounds collected on it:
# {"03.01.2026": ["RM1", "RM2", "RM4", "PPK"], ...}. RM1/RM2/RM4 are the
# weekly, two-weekly and four-weekly residual-waste rounds, which can fall on
# the same day.


@final
class Source(BaseSource):
    TITLE = "EAD Darmstadt"
    DESCRIPTION = "Source script for waste collection in Darmstadt ead.darmstadt.de"
    URL = "https://ead.darmstadt.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    IGNORE_DUPLICATES_DEFAULT = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Stresemannstraße": {"street": "Stresemannstraße"},
        "Trondheimstraße": {"street": "Trondheimstraße"},
        "Mühltalstraße": {"street": "Mühltalstraße"},
        "Heinheimer Straße": {"street": "Heinheimer Straße"},
        "Kleyerstraße": {"street": "Kleyerstraße"},
        "Untere Mühlstraße": {"street": "Untere Mühlstraße 1-29, 2-36"},
    }

    PARAMS = (street(),)

    retrieve = HttpGetRetriever(
        url="https://ead.darmstadt.de/unser-angebot/privathaushalte/abfallkalender/singleStreet/",
        params=lambda street, **_: {"type": "742394", "street": street},
    )
    parse = parsers.JsonParser()
    preprocess = FlattenGroups(with_key=True)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d.%m.%Y"),
        type_value_map={
            "RM1": wt.GENERAL_WASTE,
            "RM2": wt.GENERAL_WASTE,
            "RM4": wt.GENERAL_WASTE,
            "PPK": wt.PAPER,
            "WET": wt.RECYCLABLES,
            "BIO": wt.ORGANIC,
        },
        carry_raw_label=True,
    )
