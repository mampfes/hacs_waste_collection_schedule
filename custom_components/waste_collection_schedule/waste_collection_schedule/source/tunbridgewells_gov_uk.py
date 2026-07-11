from collections.abc import Iterable
from typing import Any, ClassVar, final

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

HOSTNAME = "mytwbc.tunbridgewells.gov.uk"
INITIAL_URL = (
    "https://mytwbc.tunbridgewells.gov.uk/AchieveForms/?mode=fill&consentMessage=yes"
    "&form_uri=sandbox-publish://AF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed/"
    "AF-Stage-88caf66c-378f-4082-ad1d-07b7a850af38/definition.json&process=1"
    "&process_uri=sandbox-processes://AF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed"
    "&process_id=AF-Process-e01af4d4-eb0f-4cfe-a5ac-c47b63f017ed"
)
LOOKUP_ID = "6314720683f30"


@final
class Source(BaseSource):
    TITLE = "Tunbridge Wells"
    DESCRIPTION = "Source for Tunbridge Wells."
    URL = "https://tunbridgewells.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "10090058289": {"uprn": "10090058289"},
        "100061204678": {"uprn": 100061204678},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        skip_landing_page=True,
        steps=[
            LookupStep(
                LOOKUP_ID,
                section="Property",
                form_values=lambda ctx, source: {
                    key: {"value": source.params["uprn"]}
                    for key in ["addressPicker", "propertyReference", "siteReference"]
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # `nextDate` is published without a year ("Friday 10 July") since the
    # collection is always in the near future; date_parsers.next_weekday
    # rolls it to whichever of this/next year puts it on/after today.
    transform = JsonTransformer(
        date_key="nextDate",
        type_key="collectionType",
        parse_date=date_parsers.next_weekday("%A %d %B"),
        type_value_map={
            "refuse": GENERAL_WASTE,
            "recycling": RECYCLABLES,
            "garden": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[dict]":
        # rows_data is a dict keyed by row index ({"0": {...}, "1": {...}}),
        # one row per collection; JsonTransformer needs each row, not the
        # whole rows_data dict as a single record.
        yield from (rows.values() if isinstance(rows, dict) else rows)
