from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _cell(column: str):
    return lambda row: row.select_one(f'td[data-eb-colheader="{column}"]').get_text(
        strip=True
    )


@final
class Source(BaseSource):
    TITLE = "Dartford Borough Council"
    DESCRIPTION = "Source for Dartford Borough Council."
    URL = "https://dartford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.GARDEN_WASTE]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100060862889"},
        "Test_002": {"uprn": 100060857499},
        "Test_003": {"uprn": "200000540020"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Your UPRN is displayed in the top left corner of the Dartford website "
            "when you are viewing your collection schedule, or look it up on "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://windmz.dartford.gov.uk/ufs/WS_CHECK_COLLECTIONS.eb",
        params=lambda uprn, **_: {"UPRN": uprn},
    )
    parse = parsers.HtmlParser('tr:has(> td[data-eb-colheader="Date"])')
    transform = HtmlTransformer(
        date_getter=_cell("Date"),
        type_getter=_cell("Collection Type"),
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "REFUSE": wt.GENERAL_WASTE,
            "RECYCLING": wt.RECYCLABLES,
            "GARDEN WASTE": wt.GARDEN_WASTE,
        },
    )
