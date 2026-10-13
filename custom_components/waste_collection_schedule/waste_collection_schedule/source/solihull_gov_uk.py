from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, uprn
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import RowTransformer

_DATE = date_parsers.for_format("%A, %d %B %Y")

# How many weeks ahead "predict" projects the next collection.
_PREDICT_WEEKS = 10


def _describe(card, source):
    """One card per bin: its type, last and next date and its frequency note."""
    title = card.select_one("div.card-title h5") or card.select_one("div.card-title h4")
    if title is None:
        return
    key = title.get_text(strip=True)
    frequency = card.select_one("div.card-title").find_next_sibling().get_text().lower()
    step = (
        recurrence.FORTNIGHTLY
        if "fortnightly" in frequency or "every other week" in frequency
        else recurrence.WEEKLY
    )
    predict = bool(source.params.get("predict"))
    for line in card.select("div.mt-1"):
        date_tag = line.find("strong")
        if date_tag is None:
            continue
        try:
            date = _DATE(date_tag.get_text(strip=True))
        except ValueError:
            continue
        if predict and "next" in line.get_text():
            yield Schedule(key, date, step, _PREDICT_WEEKS * 7 // step.days)
        else:
            yield Schedule(key, date)


@final
class Source(BaseSource):
    TITLE = "Solihull Council"
    DESCRIPTION = "Source for Solihull Council."
    URL = "https://www.solihull.gov.uk/"
    COUNTRY = "uk"

    TEST_CASES: ClassVar[dict] = {
        "100070994046": {"uprn": 100070994046},
        "200003821723, Predict": {"uprn": 200003821723, "predict": True},
        "New Garden Waste Subscription Service": {"uprn": 100071011936},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
    ]

    PARAMS = (
        uprn(),
        boolean("predict", "Predict future collections"),
    )

    RAISE_ON_EMPTY = True

    retrieve = HttpGetRetriever(
        url="https://digital.solihull.gov.uk/BinCollectionCalendar/Calendar.aspx",
        params=lambda uprn, **_: {"UPRN": uprn},
    )
    parse = parsers.HtmlParser("div.card-body div.col-xs-8")
    preprocess = RecurrenceExpander(_describe)
    transform = RowTransformer(
        type_value_map={
            "Household Waste": wt.GENERAL_WASTE,
            "Mixed Recycling": wt.RECYCLABLES,
            "Garden Waste": wt.GARDEN_WASTE,
            "Garden Waste - Subscribed": wt.GARDEN_WASTE,
            "Food Waste": wt.FOOD_WASTE,
        },
    )
