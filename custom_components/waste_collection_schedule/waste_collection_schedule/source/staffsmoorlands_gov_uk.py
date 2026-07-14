import json
import logging
import re
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Staffordshire Moorlands District Council"
DESCRIPTION = "Source for waste collection services for Staffordshire Moorlands District Council, UK."
URL = "https://www.staffsmoorlands.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "Managers Accommodation Roaring Meg (ST8 7EA)": {
        "postcode": "ST8 7EA",
        "uprn": "10010602737",
    },
    "34 Pennine Way, Biddulph (ST8 7EA)": {
        "postcode": "ST8 7EA",
        "uprn": "100031858191",
    },
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Garden Waste": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Your UPRN can be found by searching your postcode at https://www.staffsmoorlands.gov.uk/findyourbinday (which redirects to the council's Public Dashboard) and selecting your address. The value shown in the address dropdown is your UPRN. Alternatively, find your UPRN at https://www.findmyaddress.co.uk/",
}

PARAM_TRANSLATIONS: dict = {
    "en": {
        "postcode": "Postcode",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS: dict = {
    "en": {
        "postcode": "Your property postcode, e.g. ST8 7EA",
        "uprn": "Unique Property Reference Number (UPRN) for your property",
    }
}

# Staffordshire Moorlands migrated their bin day lookup from a standalone
# form (/findyourbinday, now redirects) to a Bartec Municipal "Public
# Dashboard" portal — the same platform used by highpeak_gov_uk.py (the two
# councils share back-office services), southlanarkshire_gov_uk.py and
# scotborders_gov_uk.py.
API_URL = "https://bins.staffsmoorlands.gov.uk/PublicDashboard"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

TOKEN_REGEX = re.compile(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"')
DATASOURCE_REGEX = re.compile(
    r'dataSource":\s*ejs\.data\.DataUtil\.parse\.isJson\(\s*(\[.*?\])\s*\)',
    re.DOTALL,
)


class Source:
    def __init__(self, postcode: str, uprn: str | int):
        self._postcode: str = postcode.strip()
        self._uprn: str = str(uprn).strip()

    @staticmethod
    def _get_token(html: str) -> str:
        match = TOKEN_REGEX.search(html)
        if not match:
            raise RuntimeError(
                "Could not find verification token on Staffordshire Moorlands bin day lookup page."
            )
        return match.group(1)

    @staticmethod
    def _extract_json_blocks(html: str) -> list[list[dict]]:
        blocks = []
        for raw in DATASOURCE_REGEX.findall(html):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):
                blocks.append(data)
        return blocks

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        # Step 1: load the dashboard to obtain the anti-forgery token
        r = session.get(API_URL)
        r.raise_for_status()
        token = self._get_token(r.text)

        # Step 2: search for the postcode to obtain the list of premises
        r = session.post(
            f"{API_URL}?handler=SearchPostcode",
            data={
                "__RequestVerificationToken": token,
                "SelectedPostcode": self._postcode,
            },
        )
        r.raise_for_status()
        token = self._get_token(r.text)

        premises_blocks = [
            block
            for block in self._extract_json_blocks(r.text)
            if block and "UPRN" in block[0]
        ]
        if not premises_blocks:
            raise SourceArgumentNotFound("postcode", self._postcode)

        known_uprns = sorted(
            {str(int(item["UPRN"])) for item in premises_blocks[0] if "UPRN" in item}
        )

        # Step 3: select the premises (by UPRN) to obtain the collection schedule
        r = session.post(
            f"{API_URL}?handler=SelectPrem",
            data={
                "__RequestVerificationToken": token,
                "SelectedPostcode": self._postcode,
                "SelectedPremises": self._uprn,
            },
        )
        r.raise_for_status()

        schedule_blocks = [
            block
            for block in self._extract_json_blocks(r.text)
            if block and "Subject" in block[0]
        ]
        if not schedule_blocks:
            raise SourceArgumentNotFoundWithSuggestions("uprn", self._uprn, known_uprns)

        entries = []
        for item in schedule_blocks[0]:
            subject = item.get("Subject")
            date_str = item.get("StartTime")
            if not subject or not date_str:
                continue
            try:
                date_ = datetime.fromisoformat(date_str).date()
            except ValueError:
                _LOGGER.warning("Could not parse date %s", date_str)
                continue

            entries.append(
                Collection(date=date_, t=subject, icon=ICON_MAP.get(subject))
            )

        return entries
