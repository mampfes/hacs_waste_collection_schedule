import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    AchieveFormsRowsPreprocessor,
    LookupStep,
)
from waste_collection_schedule.transformers import JsonTransformer

HOSTNAME = "plymouth-self.achieveservice.com"
INITIAL_URL = (
    "https://plymouth-self.achieveservice.com/en/AchieveForms/?form_uri=sandbox-publish://"
    "AF-Process-084d6742-3572-41ba-ac1a-430750451f9d/"
    "AF-Stage-67ba684d-0a5b-48f8-9c50-1c01cc43c396/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)

# Plymouth rebuilt their "Check your collection days" form on 2026-07-31 to add
# food waste collections. This retired the old single lookup ("5c99439d85f83",
# UPRN + next-N-collections), which now returns an empty list instead of the
# expected dict (#7210). It's been replaced by a two-step chain:
#   1. "collectiveAuthenticator" - no inputs, returns a short-lived opaque
#      "collectiveKey" token required by the real lookup.
#   2. "collectionDays" - takes the UPRN, the collectiveKey, and an explicit
#      start/end date window, and returns the actual collection rows.
AUTHENTICATOR_LOOKUP_ID = "6936e38f6d376"
COLLECTION_DAYS_LOOKUP_ID = "698b9c49a3c13"

# How far ahead to request collections for. The live form itself only asks for
# a 15-day window (today .. today+15); ask for a wider one to surface more
# upcoming collections in one fetch.
LOOKAHEAD_DAYS = 60

# collectiveWasteType values look like "Empty Food 23L" / "Empty Residual
# 240L" / "Empty Recycling 1100L" / "Empty Garden 240L" - the bin size suffix
# varies per property, so match on the waste-type keyword rather than the
# full string.
_WASTE_TYPE_KEYWORDS = ("residual", "recycling", "garden", "food")


def _extract_collective_key(response: dict, context: "dict[str, Any]") -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    row = next(iter(rows.values()), {}) if isinstance(rows, dict) else {}
    key = row.get("collectiveKey") if isinstance(row, dict) else None
    if not key:
        raise SourceArgumentException(
            "uprn", "Could not establish a session token with Plymouth's form."
        )
    context["collective_key"] = key


def _collection_days_form_values(context: "dict[str, Any]", source: BaseSource) -> dict:
    start = datetime.datetime.now()
    end = start + datetime.timedelta(days=LOOKAHEAD_DAYS)
    return {
        "collectiveUPRN": {"value": source.params["uprn"]},
        "collectiveKey": {"value": context["collective_key"]},
        "collectiveGetJobStartDate": {"value": start.strftime("%Y-%m-%dT00:00:00")},
        "collectiveGetJobEndDate": {"value": end.strftime("%Y-%m-%dT00:00:00")},
    }


def _waste_type_key(record: Any) -> str:
    raw = str(record.get("collectiveWasteType", "")).lower()
    return next((kw for kw in _WASTE_TYPE_KEYWORDS if kw in raw), raw)


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
                AUTHENTICATOR_LOOKUP_ID,
                extract=_extract_collective_key,
            ),
            LookupStep(
                COLLECTION_DAYS_LOOKUP_ID,
                form_values=_collection_days_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsRowsPreprocessor()
    # An unmapped waste-type keyword is preserved verbatim rather than
    # collapsed, in case the council introduces a new collection stream.
    transform = JsonTransformer(
        date_key="collectiveCollectionDate",
        type_key=_waste_type_key,
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "residual": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "garden": wt.GARDEN_WASTE,
            "food": wt.FOOD_WASTE,
        },
    )
