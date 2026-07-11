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
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE, RECYCLABLES

HOSTNAME = "my.portsmouth.gov.uk"
INITIAL_URL = (
    "https://my.portsmouth.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-26e27e70-f771-47b1-a34d-af276075cede/"
    "AF-Stage-cd7cc291-2e59-42cc-8c3f-1f93e132a2c9/definition.json"
    "&redirectlink=%2F&cancelRedirectLink=%2F"
)
LOOKUP_ID = "5e81ed10c0241"

# (row field, waste-type label). Each field is a "<br />"-joined list of date
# strings (not a table of rows), one per bin type.
DATE_FIELDS: tuple[tuple[str, str], ...] = (
    ("listRefDatesHTML", "refuse bin"),
    ("listRecDatesHTML", "recycling bin"),
)


@final
class Source(BaseSource):
    TITLE = "Portsmouth City Council"
    DESCRIPTION = "Source for waste collection services for Portsmouth City Council."
    URL = "https://www.portsmouth.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Fawcett Road - number": {"uprn": 1775027540},
        "Fawcett Road - string": {"uprn": "1775027540"},
        "Westbourne Road - number": {"uprn": 1775084532},
        "Westbourne Road - string": {"uprn": "1775084532"},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ID,
                no_retry="true",
                form_values=lambda ctx, source: {
                    "col_uprn": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "refuse bin": GENERAL_WASTE,
            "recycling bin": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[Any, str]]":
        if isinstance(rows, dict) and "0" in rows:
            row = rows["0"]
        elif isinstance(rows, dict):
            row = rows
        elif rows:
            row = rows[0]
        else:
            row = {}
        if not isinstance(row, dict):
            return
        for field_name, label in DATE_FIELDS:
            raw = row.get(field_name)
            if not raw:
                continue
            for entry in raw.split("<p>")[0].split("<br />"):
                if not entry:
                    continue
                yield entry.rstrip("* "), label
