import re
from collections.abc import Iterable
from datetime import date, timedelta
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, response_shape
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsRetriever,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    FOOD_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Live-verified (2026-07): the standard AchieveForms handshake
# (init_session -> authapi/isauthenticated) authenticates East Cambridgeshire's
# host without any need to regex-scrape a `sid` out of the landing-page HTML,
# despite the legacy source doing exactly that. No service-layer change needed.
HOSTNAME = "eastcambs-self.achieveservice.com"
PROCESS_ID = "2c7575a6-0139-4555-9d8a-ab504a44d989"
STAGE_ID = "94ee5097-94db-474d-bc7a-d1796e3ab83a"
INITIAL_URL = (
    f"https://{HOSTNAME}/AchieveForms/?mode=fill&consentMessage=yes"
    f"&form_uri=sandbox-publish://AF-Process-{PROCESS_ID}/AF-Stage-{STAGE_ID}/definition.json"
    "&process=1"
    f"&process_uri=sandbox-processes://AF-Process-{PROCESS_ID}"
    f"&process_id=AF-Process-{PROCESS_ID}"
)
AUTH_LOOKUP_ID = "69d8f92eea3cf"
COLLECTIONS_LOOKUP_ID = "6784e74793b68"

# The council's new provider only serves dates from this go-live date onward;
# querying an earlier window returns nothing, so the request floor is clamped
# to it (mirrors the legacy source's behaviour, not a fabricated schedule).
SERVICE_START = date(2026, 6, 1)

# A wide "BIN TYPE[ - size/count] - DD/MM/YYYY" label is split in preprocess()
# into (date, bin type); this strips the trailing size ("- 240L") or bag-count
# ("X3") qualifier so the bin type maps cleanly onto a canonical WasteType.
_SIZE_SUFFIX_RE = re.compile(r"\s*-\s*\d+L$", re.IGNORECASE)
_COUNT_SUFFIX_RE = re.compile(r"\s*X\d+$", re.IGNORECASE)


def _clean_bin_type(label: str) -> str:
    label = _SIZE_SUFFIX_RE.sub("", label)
    label = _COUNT_SUFFIX_RE.sub("", label)
    return label.strip()


def _extract_auth_token(response: dict, context: dict) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    token = rows.get("0", {}).get("AuthenticateResponse") if rows else None
    if not token:
        raise SourceArgumentException(
            "uprn", "Failed to obtain an East Cambridgeshire auth token"
        )
    context["auth_token"] = token


def _collections_form_values(context: dict, source: "BaseSource") -> dict:
    today = date.today()
    start_date = max(today, SERVICE_START)
    end_date = today + timedelta(days=90)
    return {
        "AuthenticateResponse": {"value": context["auth_token"]},
        "selected_uprn": {"value": source.params["uprn"]},
        "MinimumDateForNextDates": {"value": start_date.strftime("%Y-%m-%d")},
        "MaximumDateFormattedNext": {"value": end_date.strftime("%Y-%m-%d")},
    }


@final
class Source(BaseSource):
    TITLE = "East Cambridgeshire District Council"
    DESCRIPTION = (
        "Source for eastcambs.gov.uk, East Cambridgeshire District Council, UK"
    )
    URL = "https://www.eastcambs.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "14 Meadow Way Ely": {"uprn": 10002601730},
        "20 Forehill Ely": {"uprn": "10002597181"},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        steps=[
            LookupStep(
                AUTH_LOOKUP_ID,
                form_values=lambda ctx, source: {},
                extract=_extract_auth_token,
            ),
            LookupStep(
                COLLECTIONS_LOOKUP_ID,
                form_values=_collections_form_values,
            ),
        ],
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        clean=_clean_bin_type,
        type_value_map={
            "recycling bin": RECYCLABLES,
            "outdoor food caddy": FOOD_WASTE,
            "indoor food caddy": FOOD_WASTE,
            "rubbish bin": GENERAL_WASTE,
            "garden waste bin": GARDEN_WASTE,
            "brown bags": GENERAL_WASTE,
            "purple bags": RECYCLABLES,
            "clear bags": RECYCLABLES,
            "black bag": GENERAL_WASTE,
            # East Cambridgeshire's blue bin is general recycling, not the
            # paper-only round the shared "blue bin" alias resolves to.
            "blue bin": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn).strip())

    def parse(self, raw: dict, source: "BaseSource | None" = None) -> Any:
        select_data = (
            raw.get("integration", {}).get("transformed", {}).get("select_data")
        )
        response_shape.expect(
            isinstance(select_data, list),
            source_name=response_shape.source_name(source),
            detail="East Cambridgeshire response missing integration.transformed.select_data",
            raw=raw,
        )
        return select_data

    def preprocess(
        self, records: Any, source: "BaseSource | None" = None
    ) -> "Iterable[tuple[str, str]]":
        for item in records:
            label = str(item.get("label") or "").strip()
            # Label format: "BIN TYPE[ - size/count] - DD/MM/YYYY"; only the
            # trailing " - " separates the date from the (possibly multi-part)
            # bin type, so split off the last segment only.
            parts = label.rsplit(" - ", 1)
            if len(parts) != 2:
                continue
            bin_type, date_str = parts
            yield date_str.strip(), bin_type.strip()
