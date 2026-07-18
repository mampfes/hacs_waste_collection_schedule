import datetime
import re
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentException
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
    ORGANIC,
    RECYCLABLES,
)

# The Firmstep "AchieveForms" platform exposes the bin lookup as a two-step
# apibroker/runLookup flow. Each step is keyed by a hardcoded lookup id that
# the council embeds in the form's compiled definition. These were captured
# from the live form's network traffic; they're stable until the council
# republishes the form.
HOSTNAME = "integration.aberdeencity.gov.uk"
# The service landing page 403s a bare GET (bot-check in front of the page),
# so `skip_landing_page=True` uses it verbatim as the auth call's `uri` value,
# matching the legacy source's hand-built (double-encoded) SESSION_URL.
INITIAL_URL = f"https://{HOSTNAME}/service/bin_collection_calendar___view"
LOOKUP_ID_GET_TOKEN = "583c08ffc47fe"
LOOKUP_ID_GET_SCHEDULE = "5a3141caf4016"

# Both runLookup calls set `noRetry=true` (not the framework default `false`)
# to match the legacy source's `token_params`/`sched_params` exactly.
_NO_RETRY = "true"

_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": (
        "https://integration.aberdeencity.gov.uk/fillform/"
        "?iframe_id=fillform-frame-1&db_id="
    ),
}

# `GeneralDate1`, `MixedRecyclingDate2`, etc. — bin type prefix + DateN. The
# matching `Count<type>` rows don't end in `Date\d+` so they're skipped
# without a separate filter.
_DATE_KEY_RE = re.compile(r"^(.+?)Date\d+$")


def _extract_token(response: dict, context: dict[str, Any]) -> None:
    rows = response.get("integration", {}).get("transformed", {}).get("rows_data", {})
    row = rows.get("0") if isinstance(rows, dict) else None
    token = row.get("token") if isinstance(row, dict) else None
    if not token:
        raise SourceArgumentException(
            "uprn", "Could not establish a session token with Aberdeen's form."
        )
    context["token"] = token


def _schedule_form_values(context: dict[str, Any], source: BaseSource) -> dict:
    today = datetime.date.today()
    return {
        "nauprn": {"value": source.params["uprn"]},
        "token": {"value": context["token"]},
        "mindate": {"value": today.strftime("%Y-%m-%d")},
        "maxdate": {
            "value": (today + datetime.timedelta(days=60)).strftime("%Y-%m-%d")
        },
    }


@final
class Source(BaseSource):
    TITLE = "Aberdeen City Council"
    DESCRIPTION = (
        "Source script for the Aberdeen City Council bin collection calendar "
        "(integration.aberdeencity.gov.uk Granicus Firmstep self-service form)."
    )
    URL = "https://www.aberdeencity.gov.uk/"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "179 Skene Street, AB10 1QN": {"uprn": "9051064786"},
    }

    PARAMS = (uprn(),)

    retrieve = AchieveFormsRetriever(
        hostname=HOSTNAME,
        initial_url=INITIAL_URL,
        skip_landing_page=True,
        steps=[
            LookupStep(
                LOOKUP_ID_GET_TOKEN,
                extract=_extract_token,
                no_retry=_NO_RETRY,
                headers=lambda ctx, source: _HEADERS,
            ),
            LookupStep(
                LOOKUP_ID_GET_SCHEDULE,
                form_values=_schedule_form_values,
                no_retry=_NO_RETRY,
                headers=lambda ctx, source: _HEADERS,
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    preprocess = AchieveFormsDynamicRowsPreprocessor(
        _DATE_KEY_RE,
        split_label=True,
        parse_date=date_parsers.for_format("%A %d %B %Y"),
    )
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "general": GENERAL_WASTE,
            "recycling": RECYCLABLES,
            "mixed recycling": RECYCLABLES,
            "garden": GARDEN_WASTE,
            "food": FOOD_WASTE,
            "food and garden": ORGANIC,
        },
    )

    def __init__(self, uprn: str | int):
        super().__init__(uprn=str(uprn))
