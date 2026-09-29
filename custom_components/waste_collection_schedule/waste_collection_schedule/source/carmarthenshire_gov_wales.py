from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "Carmarthenshire County Council"
    DESCRIPTION = "Source script for carmarthenshire.gov.wales"
    URL = "https://www.carmarthenshire.gov.wales/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_1": {"uprn": 10009546468},
        "Test_2": {"uprn": "100100146591"},
        "Test_3": {"uprn": 10004876405},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    retrieve = HttpGetRetriever(
        url="https://www.carmarthenshire.gov.wales/umbraco/Surface/SurfaceRecycling/Index/",
        params=lambda uprn, **_: {"uprn": uprn, "lang": "en-GB"},
    )
    parse = parsers.HtmlLabelledDates(
        "div.bin-day-container",
        label="p.font1",
        date="p.font11",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=label_cleaner(
            remap={
                "Your next blue bag and food bin collection": "blue",
                "Your next black bag and glass box collection": "black",
                "Your next garden waste collection": "garden",
                "Your next hygiene waste collection": "Hygiene waste",
            }
        ),
        type_value_map={
            "blue": [wt.RECYCLABLES, wt.FOOD_WASTE],
            "black": [wt.GENERAL_WASTE, wt.GLASS],
            "garden": wt.GARDEN_WASTE,
        },
    )
