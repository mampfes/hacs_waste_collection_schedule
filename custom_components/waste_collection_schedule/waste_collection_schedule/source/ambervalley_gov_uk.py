import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import boolean, uprn
from waste_collection_schedule.preprocessors import (
    Compose,
    DefaultPreprocessor,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The feed carries only the next date per stream plus a weekly flag. A stream
# the address has no service for reports the sentinel 1900-01-01.
_NO_SERVICE = datetime.datetime(1900, 1, 1)

# stream -> (next-date field, weekly-flag field)
_STREAMS = {
    "REFUSE": ("refuseNextDate", "weeklyCollection"),
    "RECYCLING": ("recyclingNextDate", "weeklyCollection"),
    "GREEN": ("greenNextDate", "weeklyCollection"),
    "COMMUNAL REFUSE": ("communalRefNextDate", "communalRefWeekly"),
    "COMMUNAL RECYCLING": ("communalRycNextDate", "communalRycWeekly"),
}


def _describe(record, source):
    predict = bool(source.params.get("predict"))
    for stream, (date_key, weekly_key) in _STREAMS.items():
        first = datetime.datetime.strptime(record[date_key], "%Y-%m-%dT%H:%M:%S")
        if first == _NO_SERVICE:
            continue
        if not predict:
            yield Schedule(stream, first.date())
            continue
        step = recurrence.WEEKLY if record[weekly_key] else recurrence.FORTNIGHTLY
        yield Schedule(stream, first.date(), step, 365 // step.days)


@final
class Source(BaseSource):
    TITLE = "Amber Valley Borough Council"
    DESCRIPTION = (
        "Source for ambervalley.gov.uk services for Amber Valley Borough Council, UK."
    )
    URL = "https://ambervalley.gov.uk"
    COUNTRY = "uk"

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100030011612", "predict": True},
        "Test_002": {"uprn": "100030011654"},
        "test_003": {"uprn": 100030041980, "predict": True},
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    PARAMS = (
        uprn(),
        boolean("predict", "Predict future collections"),
    )

    retrieve = HttpGetRetriever(
        url="https://info.ambervalley.gov.uk/WebServices/AVBCFeeds/WasteCollectionJSON.asmx/GetCollectionDetailsByUPRN",
        params=lambda uprn, **_: {"uprn": uprn},
    )
    parse = parsers.JsonParser()
    # The feed is a single object: wrap it into a one-item list first.
    preprocess = Compose(DefaultPreprocessor(), RecurrenceExpander(_describe))
    transform = ICSTransformer(
        type_value_map={
            "REFUSE": wt.GENERAL_WASTE,
            "COMMUNAL REFUSE": wt.GENERAL_WASTE,
            "RECYCLING": wt.RECYCLABLES,
            "COMMUNAL RECYCLING": wt.RECYCLABLES,
            "GREEN": wt.GARDEN_WASTE,
        },
    )
