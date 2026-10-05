from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Black bin": wt.GENERAL_WASTE,
    "Blue bin": wt.PAPER,
    "Brown bin": wt.RECYCLABLES,
    "Green bin": wt.ORGANIC,
}


@final
class Source(BaseSource):
    TITLE = "Stockport Council"
    DESCRIPTION = "Source for bin collection services for Stockport Council, UK.\n Refactored with thanks from the Manchester equivalent"
    URL = "https://stockport.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ORGANIC,
    ]

    TEST_CASES: ClassVar[dict] = {
        "domestic": {"uprn": "100011460157"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    retrieve = retrievers.Request(
        lambda uprn, **_: (
            f"https://myaccount.stockport.gov.uk/bin-collections/show/{uprn}"
        ),
    )

    parse = parsers.HtmlLabelledDates(
        "div.service-item",
        label="h3",
        date=":scope",
        date_pattern=r"(?:\w+,\s*)?(\d{1,2}\s+\w+\s+\d{4})",
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d %B %Y"),
        type_value_map=_TYPE_MAP,
    )
