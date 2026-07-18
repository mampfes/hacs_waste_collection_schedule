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
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

HOSTNAME = "plymouth-self.achieveservice.com"
INITIAL_URL = (
    "https://plymouth-self.achieveservice.com/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-084d6742-3572-41ba-ac1a-430750451f9d/"
    "AF-Stage-67ba684d-0a5b-48f8-9c50-1c01cc43c396/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)
LOOKUP_ID = "5c99439d85f83"


@final
class Source(BaseSource):
    TITLE = "Plymouth City Council"
    DESCRIPTION = "Source for waste collection services for Plymouth City Council"
    URL = "https://www.plymouth.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 100040429524},
        "Test_002": {"uprn": "100040425325"},
        "Test_003": {"uprn": 100040472543},
        "Test_004": {"uprn": "100040462838"},
        "Test_005": {"uprn": 100040461084},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        auth_test_url=f"https://{HOSTNAME}/apibroker/domain/{HOSTNAME}",
        steps=[
            LookupStep(
                LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "number1": {"value": source.params["uprn"]},
                    "nextncoll": {"value": "9"},
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # Round_Type is a short provider code (DO = Domestic Brown Bin, RE =
    # Recycling Green Bin); an unmapped code is preserved verbatim rather than
    # collapsed, in case the council introduces a new round type.
    transform = JsonTransformer(
        date_key="Date",
        type_key="Round_Type",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map={
            "DO": GENERAL_WASTE,
            "RE": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())

    def preprocess(self, rows, source=None):
        # rows_data is a dict keyed by row index ({"0": {...}, "1": {...}}),
        # one row per collection; JsonTransformer needs each row, not the
        # whole rows_data dict as a single record.
        yield from (rows.values() if isinstance(rows, dict) else rows)
