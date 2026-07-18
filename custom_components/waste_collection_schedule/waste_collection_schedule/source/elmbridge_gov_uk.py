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
from waste_collection_schedule.transformers import RowTransformer, label_cleaner
from waste_collection_schedule.waste_types import (
    ELECTRONICS,
    FOOD_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "elmbridge-self.achieveservice.com"
INITIAL_URL = f"https://{HOSTNAME}/service/Your_bin_collection_days"
LOOKUP_ID = "663b557cdaece"

# Each row has one "Date" field plus up to three sibling "Service1"/"Service2"/
# "Service3" fields, each an independently-present bin service for that date.
SERVICE_FIELDS: tuple[str, ...] = ("Service1", "Service2", "Service3")


@final
class Source(BaseSource):
    TITLE = "Elmbridge Borough Council"
    DESCRIPTION = "Source for waste collection services for Elmbridge Borough Council."
    URL = "https://www.elmbridge.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"uprn": 10013119164},
        "Test_002": {"uprn": "100061309206"},
        "Test_003": {"uprn": 100062119825},
        "Test_004": {"uprn": "100061343923"},
        "Test_005": {"uprn": 100062372553},
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
                    "UPRN": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=label_cleaner(strip_suffixes=[" Collection Service"]),
        type_value_map={
            "Domestic Waste": GENERAL_WASTE,
            "Domestic Recycling": RECYCLABLES,
            "Food Waste": FOOD_WASTE,
            "Textiles and Small WEEE": ELECTRONICS,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[Any, str]]":
        values = (
            rows.values()
            if isinstance(rows, dict)
            else rows
            if isinstance(rows, list)
            else []
        )
        for row in values:
            if not isinstance(row, dict):
                continue
            date = row.get("Date")
            if not date:
                continue
            # AchieveForms sometimes appends a trailing " HH:MM:SS" to an
            # otherwise fixed-width "%d/%m/%Y" date; keep only the date part.
            date = str(date)[:10]
            for field_name in SERVICE_FIELDS:
                service = row.get(field_name)
                if not service:
                    continue
                yield date, service
