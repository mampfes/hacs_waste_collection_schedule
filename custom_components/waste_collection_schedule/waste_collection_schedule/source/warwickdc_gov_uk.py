from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer


@final
class Source(BaseSource):
    TITLE = "Warwick District Council"
    DESCRIPTION = "Source for Warwick District Council rubbish collection."
    URL = "https://www.warwickdc.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100070260258"},
        "Test_002": {"uprn": "100070258568"},
        "Test_003": {"uprn": 100070263501},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://estates7.warwickdc.gov.uk/PropertyPortal/Property/Recycling/{uprn}"
        ),
    )
    # One box per round: "Food Waste<br/>Wednesday", then a date per line.
    parse = parsers.HtmlLabelledDates(
        "div.waste-dates",
        label="strong",
        date=":scope",
        date_pattern=r"\d{2}/\d{2}/\d{4}",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        label_separator="\n",
        all_dates=True,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food Waste": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
            # The collection weekday printed under the round's name.
            **dict.fromkeys(
                ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"), None
            ),
        },
    )
