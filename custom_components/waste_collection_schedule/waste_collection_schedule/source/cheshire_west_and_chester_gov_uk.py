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
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

HOSTNAME = "my.cheshirewestandchester.gov.uk"
INITIAL_URL = (
    "https://my.cheshirewestandchester.gov.uk/en/AchieveForms/?form_uri="
    "sandbox-publish://AF-Process-0187a2f6-15cb-413a-8a3f-b6d14d63da57/"
    "AF-Stage-e18b38ff-be8a-45f4-ac14-f8821024f0c4/definition.json"
    "&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes"
)
NONCE_LOOKUP_ID = "609b918c7dd6d"
SERVICE_TYPES_LOOKUP_ID = "6101d1a29ba09"
SCHEDULE_LOOKUP_ID = "6101d23110243"

# Not every UPRN in the area shares the same service-type display name (e.g.
# Chester's "Empty Black Sacks" vs. another area's "Empty 180l Domestic"), so
# the provider's serviceTypes lookup maps each UPRN's own labels back onto
# these generic categories; only a recognised generic category is kept.
GENERIC_SERVICE_TYPES = {
    "Domestic": GENERAL_WASTE,
    "Food": FOOD_WASTE,
    "Recycling": RECYCLABLES,
    "Garden": GARDEN_WASTE,
}


def _extract_nonce(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    row0 = rows.get("0", {}) if isinstance(rows, dict) else {}
    context["nonce"] = row0.get("AuthenticateResponse", "")


def _extract_service_map(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    values = rows.values() if isinstance(rows, dict) else rows
    service_map = {}
    for row in values or []:
        generic = str(row.get("service") or "").strip()
        if generic in GENERIC_SERVICE_TYPES:
            service_map[row.get("serviceType")] = generic
    context["map"] = service_map


def _uprn_form_values(context: dict, source: Any) -> dict:
    return {
        "AuthenticateResponse": {"value": context.get("nonce", "")},
        "UPRN": {"value": source.params["uprn"]},
    }


def _schedule_form_values(context: dict, source: Any) -> dict:
    # Stash the service-type map onto the source so preprocess() can resolve
    # each row's generic waste-type label; a LookupStep's extract can only
    # mutate the retrieve chain's own context, not reach the pipeline steps
    # that run after retrieve, so form_values (which also receives source) is
    # the source-only side channel for handing it across.
    source._service_map = context.get("map", {})
    return _uprn_form_values(context, source)


@final
class Source(BaseSource):
    TITLE = "Cheshire West and Chester Council"
    DESCRIPTION = (
        "Source for waste collection services for Cheshire West and Chester Council"
    )
    URL = "https://www.cheshirewestandchester.gov.uk"
    COUNTRY = "uk"

    TEST_CASES: ClassVar[dict] = {
        "Chester": {"uprn": 100010030086},
        "Chester - string": {"uprn": "100010030086"},
        "Northwich": {"uprn": 10011715183},
        "Hartford": {"uprn": 100010181592},
        "Tarporley": {"uprn": 10014514851},
        # Knutsford is in Cheshire East, not Cheshire West and Chester, so it
        # has no collection information: this must resolve to an empty result
        # rather than an error, hence no RAISE_ON_EMPTY on this source.
        "Knutsford - no results": {"uprn": 100010132172},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                NONCE_LOOKUP_ID,
                form_values=lambda ctx, source: {},
                extract=_extract_nonce,
            ),
            LookupStep(
                SERVICE_TYPES_LOOKUP_ID,
                form_values=_uprn_form_values,
                extract=_extract_service_map,
            ),
            LookupStep(
                SCHEDULE_LOOKUP_ID,
                form_values=_schedule_form_values,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    transform = JsonTransformer(
        date_key="collectionDateTime",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%dT%H:%M:%S"),
        type_value_map=GENERIC_SERVICE_TYPES,
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))

    def preprocess(
        self, rows: Any, source: "BaseSource | None" = None
    ) -> "Iterable[dict]":
        service_map = getattr(self, "_service_map", {})
        values = rows.values() if isinstance(rows, dict) else rows
        for row in values or []:
            if not isinstance(row, dict):
                continue
            generic = service_map.get(row.get("serviceType"))
            if generic is None:
                continue
            yield {"collectionDateTime": row.get("collectionDateTime"), "type": generic}
