from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    ORGANIC,
    RECYCLABLES,
)

HOSTNAME = "portal.walthamforest.gov.uk"
INITIAL_URL = (
    "https://portal.walthamforest.gov.uk/AchieveForms/?mode=fill&consentMessage=yes"
    "&form_uri=sandbox-publish://AF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393/"
    "AF-Stage-8bf39bf9-5391-4c24-857f-0dc2025c67f4/definition.json&process=1"
    "&process_uri=sandbox-processes://AF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393"
    "&process_id=AF-Process-d62ccdd2-3de9-48eb-a229-8e20cbdd6393"
)
LOOKUP_ID = "5e208cda0d0a0"
UPRN_FIELDS = [
    "AccountSiteUprn",
    "UPRNSearch",
    "calcUPRN",
    "customerUPRN",
    "inputUPRN",
]


@final
class Source(BaseSource):
    TITLE = "Waltham Forest"
    DESCRIPTION = "Source for Waltham Forest."
    URL = "https://walthamforest.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "200001421821": {"uprn": "200001421821"},
        "100023583909": {"uprn": 100022551607},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ID,
                section="Property",
                form_values=lambda ctx, source: {
                    key: {"value": source.params["uprn"]} for key in UPRN_FIELDS
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # NextCollectionDate is published without a year ("Monday 13 July") since
    # the collection is always in the near future; date_parsers.next_weekday
    # rolls it to whichever of this/next year puts it on/after today. A
    # service the property isn't subscribed to (or with no further
    # collection scheduled) reports NextCollectionDate as " NaN "; skip
    # those rows rather than failing the whole fetch.
    transform = JsonTransformer(
        date_key="NextCollectionDate",
        type_key="ServiceName",
        parse_date=date_parsers.next_weekday("%A %d %B"),
        skip_unparseable_dates=True,
        type_value_map={
            "Domestic Waste Collection Service": GENERAL_WASTE,
            "Food Waste Collection Service": FOOD_WASTE,
            "Organic Collection Service": ORGANIC,
            "Recycling Collection Service": RECYCLABLES,
            "Garden Waste Collection Service": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))

    def preprocess(self, rows, source=None):
        # rows_data is a dict keyed by row index ({"0": {...}, "1": {...}}),
        # one row per collection; JsonTransformer needs each row, not the
        # whole rows_data dict as a single record.
        yield from (rows.values() if isinstance(rows, dict) else rows)
