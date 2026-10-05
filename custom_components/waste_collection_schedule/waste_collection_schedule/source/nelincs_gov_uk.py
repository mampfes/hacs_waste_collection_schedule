from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.service.JaduBinCollections import strip_ordinal
from waste_collection_schedule.transformers import RowTransformer

_parse = date_parsers.for_format("%d %B %Y")


@final
class Source(BaseSource):
    TITLE = "North East Lincolnshire Council"
    DESCRIPTION = "Source for North East Lincolnshire Council."
    URL = "https://www.nelincs.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "11042949": {"uprn": 11042949},
        "11043243": {"uprn": "11043243"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url="https://www.nelincs.gov.uk/refuse-collection-schedule/",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    # One card per bin, listing its upcoming dates ("Wednesday, 30th
    # September 2026").
    parse = parsers.HtmlLabelledDates(
        "#view-type div.mb-4:has(.h4)",
        label=".h4",
        date="ul",
        date_pattern=r"\d{1,2}(?:st|nd|rd|th) \w+ \d{4}",
        parse_date=lambda text: _parse(strip_ordinal(text)),
        all_dates=True,
    )
    transform = RowTransformer(
        type_value_map={
            "General Waste": wt.GENERAL_WASTE,
            "Household Waste": wt.GENERAL_WASTE,
            "Cans, Plastic & Glass": wt.RECYCLABLES,
            "Paper & Cardboard": wt.PAPER,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
