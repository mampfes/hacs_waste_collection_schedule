from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import RowTransformer, label_cleaner


@final
class Source(BaseSource):
    TITLE = "North Somerset Council"
    DESCRIPTION = "Source for n-somerset.gov.uk services for North Somerset, UK."
    URL = "n-somerset.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Walliscote Grove Road, Weston super Mare": {
            "uprn": "24009468",
            "postcode": "BS23 1UJ",
        },
        "Walliscote Road, Weston super Mare": {
            "uprn": "24136727",
            "postcode": "BS23 1EF",
        },
    }

    PARAMS = (uprn(), postcode())

    retrieve = HttpPostRetriever(
        url="https://forms.n-somerset.gov.uk/Waste/CollectionSchedule",
        data=lambda uprn, postcode, **_: {
            "PreviousHouse": "",
            "PreviousPostcode": "-",
            "Postcode": postcode,
            "SelectedUprn": uprn,
        },
    )
    # One row per service: its next and its following date, without a year.
    parse = parsers.HtmlLabelledDates(
        "tr:has(td)",
        label="td",
        date=":scope",
        date_pattern=r"[A-Z][a-z]+day \d{1,2} [A-Z][a-z]+",
        parse_date=date_parsers.nearest_year("%A %d %B"),
        all_dates=True,
    )
    transform = RowTransformer(
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "Food": wt.FOOD_WASTE,
            "Card and Paper": wt.PAPER,
            "Recycling": wt.RECYCLABLES,
            "Refuse": wt.GENERAL_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
