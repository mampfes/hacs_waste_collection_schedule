from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.transformers import RowTransformer

_TYPE_MAP = {
    "Refuse": wt.GENERAL_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Garden": wt.GARDEN_WASTE,
    "Food waste": wt.FOOD_WASTE,
}


@final
class Source(BaseSource):
    TITLE = "Blaby District Council"
    DESCRIPTION = (
        "Recycling and refuse collection dates for Blaby District Council, UK."
    )
    URL = "https://my.blaby.gov.uk/collections"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100030407500},
        "Test_002": {"uprn": "100030395499"},
        "Test_003": {"uprn": "010001238216"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)."
        ),
    }

    # The property is remembered in the session: the first request selects it,
    # the collections page then shows it.
    retrieve = retrievers.Request(
        "https://my.blaby.gov.uk/collections",
        before=(
            retrievers.Lookup(
                "https://my.blaby.gov.uk/set-location.php",
                params=lambda uprn, **_: {
                    "ref": str(uprn).zfill(12),
                    "redirect": "collections",
                },
                allow_redirects=False,
                pick=lambda response, *keys, **_: None,
            ),
        ),
    )

    parse = parsers.HtmlLabelledDates(
        "span.box-item",
        label="h2",
        date="strong",
        date_pattern=r"(\d{2}/\d{2}/\d{4})",
        all_dates=True,
    )

    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map=_TYPE_MAP,
    )
