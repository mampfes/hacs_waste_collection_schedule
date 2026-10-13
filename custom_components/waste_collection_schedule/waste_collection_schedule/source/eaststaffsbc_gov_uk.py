from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.service.JaduBinCollections import strip_ordinal
from waste_collection_schedule.transformers import RowTransformer

API_URL = "https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates"

# The block's text runs together with its bin labels ("...OctoberBlue Bag"), so
# the month has to be matched by name rather than as a word.
_DATE_PATTERN = (
    r"\w+, \d+(?:st|nd|rd|th) "
    r"(?:January|February|March|April|May|June|July|August|September|October"
    r"|November|December)"
)

_NEAREST_YEAR = date_parsers.nearest_year("%A, %d %B")


def _date(text: str):
    """ "Tuesday, 13th October" -> the date, the year being the nearest to today."""
    return _NEAREST_YEAR(strip_ordinal(text))


@final
class Source(BaseSource):
    TITLE = "East Staffordshire Borough Council"
    DESCRIPTION = "Source for East Staffordshire Borough Council"
    URL = "https://www.eaststaffsbc.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Marlpit Lane": {"uid": 103368},
        "Church Lane": {"uid": "103281"},
    }

    PARAMS = (location_id("uid"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Search for your address on the "
            "[East Staffordshire collection dates page]"
            "(https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates). "
            "The number at the end of the resulting address "
            "(`.../collection-dates/<uid>`) is your `uid`."
        ),
    }

    retrieve = retrievers.HttpGetRetriever(url=lambda uid, **_: f"{API_URL}/{uid}")

    # The "next collection" block and every later date are each one block with
    # its own date line and the bins collected that day.
    parse = parsers.HtmlLabelledDates(
        ".collection-next, .bin_collections > li",
        label=".containers .field__item",
        all_labels=True,
        date=":scope",
        date_pattern=_DATE_PATTERN,
        parse_date=_date,
    )

    transform = RowTransformer(
        type_value_map={
            "Blue Bin": wt.RECYCLABLES,
            "Brown Bin": wt.GARDEN_WASTE,
            "Weekly Food Waste": wt.FOOD_WASTE,
            "Blue Bag": wt.PAPER,
            "Grey Bin": wt.GENERAL_WASTE,
        },
    )
