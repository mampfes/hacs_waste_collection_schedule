import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsFieldMapPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    GetStep,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "spelthorne-self.achieveservice.com"
BASE_URL = f"https://{HOSTNAME}"
TOKEN_LOOKUP_ID = "5f97e6e09fedd"
COLLECTION_LOOKUP_ID = "66042a164c9a5"


def _extract_csrf(response: dict, context: dict) -> None:
    context["csrf"] = response.get("data", {}).get("csrfToken", "")


def _extract_token_string(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    context["token"] = rows.get("0", {}).get("tokenString", "")


def _collection_form_values(context: dict, source: Any) -> dict:
    today = datetime.date.today()
    return {
        "token": {"value": context["token"]},
        "uprn1": {"value": source.params["uprn"]},
        "last2Weeks": {"value": (today - datetime.timedelta(days=14)).isoformat()},
        "endDate": {"value": (today + datetime.timedelta(days=90)).isoformat()},
    }


@final
class Source(BaseSource):
    TITLE = "Spelthorne Borough Council"
    DESCRIPTION = "Source for Spelthorne Borough Council, Surrey, UK."
    URL = "https://www.spelthorne.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "241 Thames Side Chertsey": {"uprn": "33042469"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find your UPRN by visiting "
            "https://spelthorne-self.achieveservice.com/service/Waste_Collections "
            "and searching for your address. Your UPRN can also be found at "
            "https://www.findmyaddress.co.uk/."
        ),
    }

    # Spelthorne needs a bare GET to a council-specific CSRF endpoint (not a
    # runLookup call at all -- GetStep), then a GET-mode runLookup to fetch a
    # one-time token (LookupStep(method="GET")), before the real POST lookup,
    # which must carry the CSRF token as a request header rather than a form
    # field (LookupStep(headers=...)).
    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        service_page="Waste_Collections",
        auth_test_url=f"{BASE_URL}/apibroker/domain/{HOSTNAME}",
        steps=[
            GetStep(
                f"{BASE_URL}/api/nextref",
                extract=_extract_csrf,
            ),
            LookupStep(
                TOKEN_LOOKUP_ID,
                method="GET",
                no_retry="true",
                extract=_extract_token_string,
            ),
            LookupStep(
                COLLECTION_LOOKUP_ID,
                section="Property details",
                no_retry="true",
                form_values=_collection_form_values,
                headers=lambda ctx, source: {"X-CSRF-Token": ctx["csrf"]},
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsFieldMapPreprocessor(
        fields=[
            ("GwPrevCollection", "Garden Waste"),
            ("GwNextCollection", "Garden Waste"),
            ("RefPrevCollection", "Refuse"),
            ("RefNextCollection", "Refuse"),
            ("RecPrevCollection", "Recycling"),
            ("RecNextCollection", "Recycling"),
        ],
    )
    transform = RowTransformer(
        type_value_map={
            "garden waste": GARDEN_WASTE,
            "refuse": GENERAL_WASTE,
            "recycling": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())
