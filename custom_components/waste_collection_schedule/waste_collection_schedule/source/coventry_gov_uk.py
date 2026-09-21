import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

TITLE = "Coventry City Council"
DESCRIPTION = "Source for waste collection services for Coventry City Council"
URL = "https://www.coventry.gov.uk/"
COUNTRY = "uk"

HOST = "myaccount.coventry.gov.uk"
BASE_URL = f"https://{HOST}"
LOOKUP_ID = "6a675c200be8f"

TEST_CASES = {
    "Test_001": {"uprn": "100070666040"},
    "Test_002": {"uprn": 100070666041},
    "Test_003": {"uprn": "100070649599"},
}

# Result column -> (waste type, icon)
WASTE_TYPES = {
    "Bartec_Refuse_Date": ("Household waste (green-lidded bin)", Icons.GENERAL_WASTE),
    "Bartec_Recycling_Date": ("Recycling (blue-lidded bin)", Icons.RECYCLING),
    "Bartec_Garden_Date": ("Garden waste (brown-lidded bin)", Icons.GARDEN),
    "Bartec_Food_Date": ("Food waste caddy", Icons.BIO_KITCHEN),
}

PARAM_TRANSLATIONS = {
    "en": {"uprn": "Property reference number (UPRN)"},
}
PARAM_DESCRIPTIONS = {
    "en": {"uprn": "Unique Property Reference Number of your address"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.",
}


class Source:
    def __init__(self, uprn: str | int | None = None):
        if uprn is None or str(uprn).strip() == "":
            raise SourceArgumentRequired(
                "uprn",
                "Coventry replaced its street lookup with an address lookup; "
                "find your UPRN at https://www.findmyaddress.co.uk/",
            )
        self._uprn = str(uprn).strip()

    def fetch(self) -> list[Collection]:
        s = requests.Session()
        s.headers.update({"User-Agent": "Mozilla/5.0"})
        sid = init_session(
            s,
            initial_url=f"{BASE_URL}/service/find_my_bin_day",
            auth_url=f"{BASE_URL}/authapi/isauthenticated",
            hostname=HOST,
        )
        data = run_lookup(
            s,
            api_url=f"{BASE_URL}/apibroker/runLookup",
            sid=sid,
            lookup_id=LOOKUP_ID,
            form_values={"Section 1": {"Address_UPRN": {"value": self._uprn}}},
        )
        xml = data.get("data") or ""
        results = dict(re.findall(r'column="(\w+)" isNull="False">([^<]*)<', xml))

        if results.get("Bartec_Error", "false").lower() == "true":
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                results.get("Bartec_Error_Message") or "Lookup returned an error.",
            )

        entries: list[Collection] = []
        for column, (waste_type, icon) in WASTE_TYPES.items():
            value = results.get(column)
            if not value:
                continue
            date = datetime.fromisoformat(value).date()
            if date.year <= 1:  # 0001-01-01 means no collection for this bin
                continue
            entries.append(Collection(date=date, t=waste_type, icon=icon))

        if not entries:
            raise SourceArgumentNotFound(
                "uprn",
                self._uprn,
                "No collections found; check the UPRN is a Coventry address.",
            )
        return entries
