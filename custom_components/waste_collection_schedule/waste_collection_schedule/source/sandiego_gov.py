from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "City of San Diego"
    DESCRIPTION = "Source for the City of San Diego."
    URL = "https://www.sandiego.gov/"
    COUNTRY = "us"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"id": "a4Ot0000000fEYZEA2"},
        "Test_002": {"id": "a4Ot0000001EEsyEAG"},
        "Test_003": {"id": "a4Ot0000000eANbEAM"},
    }

    PARAMS = (text_field("id", "Collection schedule id"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search your address on https://getitdone.sandiego.gov/apex/CollectionMapLookup, "
            "click 'Bookmarkable Page', and copy the id from the schedule page's URL."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://getitdone.sandiego.gov/CollectionDetail",
        params=lambda id, **_: {"id": id},
    )
    parse = parsers.HtmlLabelledDates(
        "div.four.columns:has(h3)",
        label="h3",
        date="p.date",
        parse_date=date_parsers.for_format("%m/%d/%Y"),
    )
    transform = RowTransformer(
        type_value_map={
            "Trash": wt.GENERAL_WASTE,
            "Recyclables": wt.RECYCLABLES,
            "Organic Waste": wt.ORGANIC,
            "Greens": wt.ORGANIC,
            "Organics": wt.ORGANIC,
        },
    )
