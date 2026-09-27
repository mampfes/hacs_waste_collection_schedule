from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "City of York Council"
    DESCRIPTION = "Source for York.gov.uk services for the city of York, UK."
    URL = "https://york.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Reighton Avenue, York": {"uprn": "100050580641"},
        "Granary Walk, York": {"uprn": "010093236548"},
    }

    PARAMS = (uprn(),)

    retrieve = HttpGetRetriever(
        url=lambda uprn, **_: (
            f"https://waste-api.york.gov.uk/api/Collections/GetBinCalendarDataForUprn/{uprn}"
        ),
    )
    parse = parsers.JsonParser("collections")
    # A round not yet scheduled carries no parsable date and is skipped.
    transform = JsonTransformer(
        date_key="date",
        type_key="roundType",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        skip_unparseable_dates=True,
        type_value_map={
            "REFUSE": wt.GENERAL_WASTE,
            "RECYCLING": wt.RECYCLABLES,
            "GARDEN": wt.GARDEN_WASTE,
        },
    )
