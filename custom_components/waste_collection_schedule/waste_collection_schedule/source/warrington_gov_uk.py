from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import Compose, Deduplicate, RowFilter
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer

_BINS = ("BLACK", "BLUE", "GREEN")


def _bin(job) -> str | None:
    """The bin a job empties: its name carries the colour, nothing else does."""
    return next((colour for colour in _BINS if colour in job["Name"]), None)


@final
class Source(BaseSource):
    TITLE = "Warrington Borough Council"
    DESCRIPTION = (
        "Source for warrington.gov.uk services for Warrington Borough Council, UK."
    )
    URL = "https://www.warrington.gov.uk"
    COUNTRY = "uk"
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100010309878"},
        "Test_002": {"uprn": "100010296572"},
        "Test_003": {"uprn": 100010291332},
        "Test_004": {"uprn": 100010258176},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            "https://www.warrington.gov.uk/bin-collections/get-jobs/"
            f"{str(uprn).zfill(12)}"
        ),
    )
    # The job list repeats a bin's collection once per job on that day.
    parse = parsers.JsonParser("schedule")
    preprocess = Compose(
        RowFilter(lambda job, _source: _bin(job) is not None),
        Deduplicate(key=lambda job: (job["ScheduledStart"][:10], _bin(job))),
    )
    transform = JsonTransformer(
        date_key=lambda job: job["ScheduledStart"][:10],
        type_key=lambda job: f"{_bin(job)} BIN",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "BLACK BIN": wt.GENERAL_WASTE,
            "BLUE BIN": wt.RECYCLABLES,
            "GREEN BIN": wt.GARDEN_WASTE,
        },
    )
