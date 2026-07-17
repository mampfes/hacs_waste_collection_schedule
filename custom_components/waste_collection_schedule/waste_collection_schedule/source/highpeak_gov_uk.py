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

TITLE = "High Peak Borough Council"
DESCRIPTION = "Source for High Peak Borough Council."
URL = "https://www.highpeak.gov.uk/"
TEST_CASES = {
    "SK23 6BQ 10010724045": {"postcode": "SK23 6BQ", "uprn": 10010724045},
    "S33 7ZA, 10010747174": {"postcode": "S33 7ZA", "uprn": "10010747174"},
    " SK13 2AD, 10010734345": {"postcode": "SK13 2AD", "uprn": "10010734345"},
}

ICON_MAP = {
    "Rubbish": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
    "Organic": Icons.BIO_KITCHEN,
    "Food": Icons.BIO_KITCHEN,
    "Garden": Icons.GARDEN,
}

# High Peak Borough Council migrated their bin day lookup from a standalone
# form (article/6348/Find-your-bin-day, now 404) to a Bartec Municipal
# "Public Dashboard" portal. See southlanarkshire_gov_uk.py /
# scotborders_gov_uk.py for other sources using the same Bartec platform.
API_URL = "https://bins.highpeak.gov.uk/PublicDashboard"

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
            raise Exception(
                "Could not find verification token on High Peak bin day lookup page."
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
