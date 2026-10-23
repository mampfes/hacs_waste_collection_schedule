from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Brown": wt.RECYCLABLES,
    "Green": wt.ORGANIC,
    "Grey": wt.GENERAL_WASTE,
    "Blue": wt.PAPER,
}


@final
class Source(BaseSource):
    TITLE = "Oldham Council"
    DESCRIPTION = "Source for Oldham Council."
    URL = "https://oldham.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 422000125973},
        "Test_002": {"uprn": "422000129104"},
        "Test_003": {"uprn": 422000042299},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and entering your address details."
        ),
    }

    retrieve = retrievers.Request(
        "https://portal.oldham.gov.uk/bincollectiondates/details",
        params=lambda uprn, **_: {"uprn": str(uprn)},
    )

    parse = parsers.HtmlLabelledDates(
        "table.data-table.confirmation",
        label="th",
        date="td.coltwo",
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=_TYPE_MAP,
    )
