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
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "your.burnley.gov.uk"
INITIAL_URL = (
    "https://your.burnley.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-b41dcd03-9a98-41be-93ba-6c172ba9f80c/"
    "AF-Stage-edb97458-fc4d-4316-b6e0-85598ec7fce8/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)
LOOKUP_ID = "607fe757df87c"


@final
class Source(BaseSource):
    TITLE = "Burnley Council"
    DESCRIPTION = "Source for burnley.gov.uk services for the Burnley, UK."
    URL = "https://burnley.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": "100010341681"},
        "Test_002": {"uprn": 100010358864},
        "Test_003": {"uprn": "100010357864"},
        "Test_004": {"uprn": 100010327003},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        skip_landing_page=True,
        auth_test_url=f"https://{HOSTNAME}/apibroker/domain/{HOSTNAME}",
        steps=[
            LookupStep(
                LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "case_uprn1": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # `display` is a single "<type> - <weekday> <day> <month>" string with no
    # year (the collection is always in the near future); date_parsers.next_weekday
    # rolls it to whichever of this/next year puts it on/after today.
    transform = JsonTransformer(
        date_key=lambda r: r["display"].split(" - ")[1],
        type_key=lambda r: r["display"].split(" - ")[0],
        parse_date=date_parsers.next_weekday("%A %d %B"),
        type_value_map={
            "refuse": GENERAL_WASTE,
            "recycling": RECYCLABLES,
            "garden": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).zfill(12))

    def preprocess(self, rows, source=None):
        # rows_data is a dict keyed by row index ({"0": {...}, "1": {...}}),
        # one row per collection; JsonTransformer needs each row, not the
        # whole rows_data dict as a single record.
        yield from (rows.values() if isinstance(rows, dict) else rows)
