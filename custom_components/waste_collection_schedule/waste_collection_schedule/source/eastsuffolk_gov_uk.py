import datetime
import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "East Suffolk Council"
DESCRIPTION = "Source for East Suffolk Council, UK."
URL = "https://www.eastsuffolk.gov.uk"
TEST_CASES = {
    "106 Mill Lane, Felixstowe, IP11 2LL": {"uprn": "100091126543"},
    "82 Mill Lane, Felixstowe, IP11 2LL": {"uprn": 100091126520},
}
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Find your UPRN by visiting "
        "https://my.eastsuffolk.gov.uk/service/Bin_collection_dates_finder "
        "and searching for your address. Your UPRN can also be found at "
        "https://www.findmyaddress.co.uk/."
    )
}
PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "UPRN",
    }
}
PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN) for your address.",
    }
}
COUNTRY = "uk"

BASE_URL = "https://my.eastsuffolk.gov.uk"
SERVICE_URL = f"{BASE_URL}/service/Bin_collection_dates_finder"
AUTH_URL = f"{BASE_URL}/authapi/isauthenticated"
API_URL = f"{BASE_URL}/apibroker/runLookup"
HOSTNAME = "my.eastsuffolk.gov.uk"

AUTH_LOOKUP_ID = "59e73f8bd860c"
COLLECTIONS_LOOKUP_ID = "68f900a32e7a4"

ICON_MAP = {
    "PAPER": Icons.PAPER,
    "CARDBOARD": Icons.PAPER,
    "FOOD": Icons.BIO_KITCHEN,
    "GENERAL": Icons.GENERAL_WASTE,
    "RESIDUAL": Icons.GENERAL_WASTE,
    "RECYCLING": Icons.RECYCLING,
    "GARDEN": Icons.GARDEN,
}

# Strip the leading emoji glyph that the API embeds in front of the label,
# e.g. "\U0001F4F0  Paper and cardboard - standard bin" -> "Paper and
# cardboard - standard bin"
LEADING_EMOJI_RE = re.compile(r"^[^A-Za-z]+")


def _get_icon(waste_type: str) -> str | None:
    upper = waste_type.upper()
    for key, icon in ICON_MAP.items():
        if key in upper:
            return icon
    return None


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        sid = init_session(session, SERVICE_URL, AUTH_URL, HOSTNAME)

        auth_result = run_lookup(
            session,
            API_URL,
            sid,
            AUTH_LOOKUP_ID,
            {"Details": {"bartecMode": {"value": "Live"}}},
        )
        auth_rows = (
            auth_result.get("integration", {}).get("transformed", {}).get("rows_data")
        )
        auth_token = ""
        if isinstance(auth_rows, dict):
            auth_token = auth_rows.get("0", {}).get("AuthenticateResponse", "")

        if not auth_token:
            raise SourceArgumentNotFound("uprn", self._uprn)

        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=90)

        col_result = run_lookup(
            session,
            API_URL,
            sid,
            COLLECTIONS_LOOKUP_ID,
            {
                "Details": {
                    "bartecMode": {"value": "Live"},
                    "AuthenticateResponse": {"value": auth_token},
                    "finalUPRN": {"value": self._uprn},
                    "minimum_date": {"value": today.strftime("%Y-%m-%dT00:00:00")},
                    "maximum_date": {"value": end_date.strftime("%Y-%m-%dT00:00:00")},
                }
            },
        )
        rows = col_result.get("integration", {}).get("transformed", {}).get("rows_data")

        if not isinstance(rows, dict) or not rows:
            raise SourceArgumentNotFound("uprn", self._uprn)

        entries = []
        for row in rows.values():
            date_str = row.get("CollectionDateFormatted", "").strip()
            if not date_str:
                continue
            try:
                collection_date = datetime.datetime.strptime(
                    date_str, "%d/%m/%Y"
                ).date()
            except ValueError:
                continue

            waste_type = LEADING_EMOJI_RE.sub(
                "", row.get("CollectionTypeDescriptive", "")
            ).strip()
            if not waste_type:
                waste_type = row.get("CollectionType", "").strip()
            if not waste_type:
                continue

            entries.append(
                Collection(
                    date=collection_date,
                    t=waste_type,
                    icon=_get_icon(waste_type),
                )
            )

        return entries
