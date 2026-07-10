from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsJsonRowsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "my.hounslow.gov.uk"
TOKEN_LOOKUP_ID = "655f4290810cf"
JOBS_LOOKUP_ID = "659eb39b66d5a"
TIMEOUT = 30


def _extract_bartec_token(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    if not rows:
        raise SourceArgumentException(
            "uprn", "Failed to get Bartec token for this UPRN"
        )
    context["bartec_token"] = rows["0"]["bartecToken"]


def _jobs_form_values(context: dict, source: Any) -> dict:
    today = date.today()
    six_months = today + timedelta(days=182)
    return {
        "searchUPRN": {"value": source.params["uprn"]},
        "bartecToken": {"value": context["bartec_token"]},
        "searchFromDate": {"value": today.isoformat()},
        "searchToDate": {"value": six_months.isoformat()},
    }


@final
class Source(BaseSource):
    TITLE = "London Borough of Hounslow"
    DESCRIPTION = "Source for London Borough of Hounslow."
    URL = "https://hounslow.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "10090801236": {"uprn": 10090801236},
        "100021552942": {"uprn": 100021552942},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        service_page="Waste_and_recycling_collections",
        auth_test_url=f"https://{HOSTNAME}/apibroker/domain/{HOSTNAME}",
        timeout=TIMEOUT,
        steps=[
            LookupStep(
                TOKEN_LOOKUP_ID,
                form_values=lambda ctx, source: {
                    "searchUPRN": {"value": source.params["uprn"]}
                },
                extract=_extract_bartec_token,
                timeout=TIMEOUT,
            ),
            LookupStep(
                JOBS_LOOKUP_ID,
                form_values=_jobs_form_values,
                timeout=TIMEOUT,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsJsonRowsPreprocessor(
        json_field="jobsJSON",
        dedupe_key=lambda item: (
            item.get("jobDate"),
            item.get("jobType") or item.get("jobName"),
        ),
    )
    transform = JsonTransformer(
        date_key="jobDate",
        type_key=lambda r: r.get("jobType") or r.get("jobName") or "Unknown",
        type_value_map={
            "residual": GENERAL_WASTE,
            "recycling": RECYCLABLES,
            "food": FOOD_WASTE,
            "garden": GARDEN_WASTE,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))
