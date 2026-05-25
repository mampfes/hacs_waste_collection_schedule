import datetime
import re
import time

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
)

TITLE = "Aberdeen City Council"
DESCRIPTION = (
    "Source script for the Aberdeen City Council bin collection calendar "
    "(integration.aberdeencity.gov.uk Granicus Firmstep self-service form)."
)
URL = "https://www.aberdeencity.gov.uk/"
COUNTRY = "uk"

# The Firmstep "AchieveForms" platform exposes the bin lookup as a two-step
# apibroker/runLookup flow. Each step is keyed by a hardcoded lookup id that
# the council embeds in the form's compiled definition. These were captured
# from the live form's network traffic; they're stable until the council
# republishes the form.
LOOKUP_ID_GET_TOKEN = "583c08ffc47fe"
LOOKUP_ID_GET_SCHEDULE = "5a3141caf4016"

SESSION_URL = (
    "https://integration.aberdeencity.gov.uk/authapi/isauthenticated"
    "?uri=https%253A%252F%252Fintegration.aberdeencity.gov.uk%252Fservice"
    "%252Fbin_collection_calendar___view"
    "&hostname=integration.aberdeencity.gov.uk&withCredentials=true"
)
API_URL = "https://integration.aberdeencity.gov.uk/apibroker/runLookup"

TEST_CASES = {
    "179 Skene Street, AB10 1QN": {"uprn": "9051064786"},
}

# Aberdeen reports waste types as compact identifiers (no spaces) — the
# API returns rows keyed `GeneralDate1`, `RecyclingDate1`, `GardenDate1`,
# etc. plus matching `Count<type>` totals. Verified by hitting the live
# endpoint with a known-invalid UPRN: returns `CountGarden`, `CountRecycling`,
# `CountGeneral` so those three are the canonical streams. Map covers
# observed types plus reasonable guesses for households that subscribe to
# additional services (food, mixed recycling) — extra unmapped names just
# return without an icon, no breakage.
ICON_MAP = {
    "General": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Mixed Recycling": Icons.RECYCLING,
    "Garden": Icons.GARDEN,
    "Food": Icons.BIO_KITCHEN,
    "Food and Garden": Icons.ORGANIC,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN (Unique Property Reference Number) for your address "
        "using https://www.findmyaddress.co.uk/ or your council documents."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (required)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "UPRN",
    },
}


# `GeneralWasteDate1`, `MixedRecyclingDate2`, etc. — bin type prefix + DateN.
_DATE_KEY_RE = re.compile(r"^(.*?)Date\d+$")
_COUNT_KEY_RE = re.compile(r"^Count")

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


def _split_camel(name: str) -> str:
    """`GeneralWaste` -> `General Waste`, `MixedRecycling` -> `Mixed Recycling`.

    The API returns waste-type names as Pascal-case identifiers; split them
    on capital-letter boundaries so the icon map and user-visible labels
    line up.
    """
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        # Step 1: obtain a sid + a request-specific token. The token is
        # returned by the first runLookup call and bound to this session.
        auth_resp = session.get(SESSION_URL, headers=_HEADERS, timeout=30)
        auth_resp.raise_for_status()
        try:
            sid = auth_resp.json()["auth-session"]
        except (ValueError, KeyError) as err:
            raise SourceArgumentException(
                "uprn",
                f"Could not establish session with Aberdeen form: {err}",
            ) from err

        token_params = {
            "id": LOOKUP_ID_GET_TOKEN,
            "repeat_against": "",
            "noRetry": "true",
            "getOnlyTokens": "undefined",
            "log_id": "",
            "app_name": "AF-Renderer::Self",
            "_": str(int(time.time() * 1000)),
            "sid": sid,
        }
        token_resp = session.post(
            API_URL, headers=_HEADERS, params=token_params, timeout=30
        )
        token_resp.raise_for_status()
        try:
            token_row = token_resp.json()["integration"]["transformed"]["rows_data"]["0"]
            token = token_row["token"]
        except (ValueError, KeyError, TypeError) as err:
            raise SourceArgumentException(
                "uprn",
                f"Aberdeen token request returned unexpected payload: {err}",
            ) from err

        # Step 2: fetch the schedule for the UPRN.
        today = datetime.date.today()
        payload = {
            "formValues": {
                "Section 1": {
                    "nauprn": {"value": self._uprn},
                    "token": {"value": token},
                    "mindate": {"value": today.strftime("%Y-%m-%d")},
                    "maxdate": {
                        "value": (today + datetime.timedelta(days=60)).strftime(
                            "%Y-%m-%d"
                        )
                    },
                }
            }
        }
        sched_params = dict(token_params)
        sched_params["id"] = LOOKUP_ID_GET_SCHEDULE
        sched_params["_"] = str(int(time.time() * 1000))

        sched_resp = session.post(
            API_URL,
            headers=_HEADERS,
            params=sched_params,
            json=payload,
            timeout=30,
        )
        sched_resp.raise_for_status()
        try:
            rows = sched_resp.json()["integration"]["transformed"]["rows_data"]["0"]
        except (ValueError, KeyError, TypeError) as err:
            raise SourceArgumentException(
                "uprn",
                f"Aberdeen schedule request returned unexpected payload: {err}",
            ) from err

        if not isinstance(rows, dict) or not rows:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collection data returned for this UPRN.",
            )

        # Aberdeen's API responds to an *invalid* UPRN with only `Count<type>`
        # rows holding `"0"` and zero `<type>Date<n>` keys. Distinguish that
        # case from a real "API changed" failure: if no date keys exist at
        # all, it's a not-found, not a parsing bug.
        has_date_keys = any(_DATE_KEY_RE.match(k) for k in rows)
        if not has_date_keys:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collections found for this UPRN. Check the number is "
                "correct and that the property is within the City of Aberdeen.",
            )

        entries: list[Collection] = []
        for key, value in rows.items():
            if _COUNT_KEY_RE.match(key):
                continue
            m = _DATE_KEY_RE.match(key)
            if not m or not value:
                continue
            bin_type_camel = m.group(1)
            bin_type = _split_camel(bin_type_camel)
            try:
                # API returns "Tuesday 28 January 2026" — locale-stable English
                date = datetime.datetime.strptime(value, "%A %d %B %Y").date()
            except (ValueError, TypeError):
                continue
            entries.append(
                Collection(
                    date=date,
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        if not entries:
            raise SourceArgumentException(
                "uprn",
                f"Aberdeen returned {len(rows)} rows including date keys but "
                "none parsed. The API format may have changed.",
            )

        return entries
