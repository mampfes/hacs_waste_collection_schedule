import re
from collections.abc import Iterable
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field, uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsDynamicRowsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    PAPER,
    RECYCLABLES,
)

HOSTNAME = "highland-self.achieveservice.com"
INITIAL_URL = f"https://{HOSTNAME}/en/service/Check_your_household_bin_collection_days"
LOOKUP_ID = "660d44a698632"

# Highland's row carries the SAME bin type twice: `<type>NextDate` plus
# `<type>NextDateNew`/`<type>NextDateOld` variants of every field. `use_new`
# (a row-wide switch derived from whether any *New value is populated) picks
# which variant is authoritative for this property.
_KEY_PATTERN = re.compile(r"^([a-z]+)NextDate(?:New|Old)?$")


def _use_new(row: dict) -> bool:
    return any(k.endswith("New") and v for k, v in row.items())


def _variant_filter(key: str, row: dict) -> bool:
    if key.endswith("New"):
        return _use_new(row)
    if key.endswith("Old"):
        return not _use_new(row)
    return True


_FREQUENCY_RE = re.compile(r"every\s+(\d+)?\s*weeks?", re.IGNORECASE)


def _weeks(frequency: str) -> "int | None":
    """Parse "every week" / "every 2 weeks" into a week count, or None."""
    match = _FREQUENCY_RE.search(frequency or "")
    if not match:
        return None
    return int(match.group(1)) if match.group(1) else 1


@final
class Source(BaseSource):
    TITLE = "Highland"
    DESCRIPTION = "Source for Highland."
    URL = "https://www.highland.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Allangrange Mains Road, Black Isle": {"uprn": 130108578, "predict": "true"},
        "Kishorn, Wester Ross": {"uprn": "130066519", "predict": "true"},
        "Quarry Lane, Tain": {"uprn": "130007199"},
        "130143631": {"uprn": 130072429, "predict": "true"},
    }

    PARAMS = (
        uprn(),
        text_field(
            "predict",
            "Predict future collections",
            default="false",
            optional=True,
        ),
    )

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                LOOKUP_ID,
                section="Your address",
                form_values=lambda ctx, source: {
                    "propertyuprn": {"value": source.params["uprn"]}
                },
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "refuse": GENERAL_WASTE,
            "recycle": RECYCLABLES,
            "garden": GARDEN_WASTE,
            "food": FOOD_WASTE,
            "containers": RECYCLABLES,
            "fibres": PAPER,
        },
    )

    def __init__(self, uprn: str | int, predict: str | bool = False):
        super().__init__(
            uprn=str(uprn),
            predict=str(predict).strip().lower() in {"true", "yes", "1"},
        )

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[Any, str]]":
        row = rows.get("0", {}) if isinstance(rows, dict) else {}
        if not isinstance(row, dict):
            return
        use_new = _use_new(row)
        suffix = "New" if use_new else "Old"
        for collection_date, label in AchieveFormsDynamicRowsPreprocessor(
            _KEY_PATTERN, key_filter=_variant_filter
        )(rows, source):
            yield collection_date, label
            if not self.params.get("predict"):
                continue
            weeks = _weeks(row.get(f"{label}Frequency{suffix}", ""))
            if not weeks:
                continue
            # 10 further occurrences at the parsed cadence, matching the
            # legacy source's fixed look-ahead window.
            for future_date in recurrence.recurring(
                collection_date, recurrence.WEEKLY * weeks, 10
            )[1:]:
                yield future_date, label
