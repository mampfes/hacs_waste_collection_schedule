import datetime
import re

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "South Holland District Council"
DESCRIPTION = "Source for South Holland District Council."
URL = "https://www.sholland.gov.uk/"

TEST_CASES = {
    "10002546801": {"uprn": 10002546801, "postcode": "PE11 2FR"},
    "PE12 7AR": {"uprn": "100030897036", "postcode": "PE12 7AR"},
}

ICON_MAP = {
    "refuse": Icons.GENERAL_WASTE,
    "garden": Icons.GARDEN,
    "recycling": Icons.RECYCLING,
    "paper": Icons.PAPER,
    "food": Icons.BIO_KITCHEN,
}

TYPE_LABELS = {
    "refuse": "Refuse",
    "recycling": "Recycling",
    "paper": "Paper and Card",
    "food": "Food Waste",
    "garden": "Garden",
}

API_URL = "https://www.sholland.gov.uk/apiserver/ajaxlibrary"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.sholland.gov.uk/mycollections",
}


class Source:
    def __init__(self, uprn: str | int, postcode: str):
        self._uprn = str(uprn)
        self._postcode = postcode

    @staticmethod
    def _parse_iso_date(date_str: str | None) -> datetime.date | None:
        if not date_str:
            return None
        try:
            return datetime.date.fromisoformat(date_str)
        except ValueError:
            return None

    def _parse_display_date(self, date_str: str) -> datetime.date | None:
        if not date_str:
            return None

        # sanitize
        clean = re.sub(r"(\d)(st|nd|rd|th)", r"\1", date_str)
        clean = clean.replace("*", "")
        clean = clean.split("(")[0].strip()
        today = datetime.date.today()

        # try with year first, if not possible calculate year
        for fmt in ("%A %d %B %Y", "%A %d %B"):
            try:
                dt = datetime.datetime.strptime(clean, fmt)
                if fmt == "%A %d %B":
                    dt = dt.replace(year=today.year)
                d = dt.date()
                if d < today:
                    d = d.replace(year=d.year + 1)
                return d
            except ValueError:
                continue
        return None

    def fetch(self):
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "SouthHolland.Waste.getCollectionDaysAjax",
            "params": {"UPRN": self._uprn},
        }

        with requests.Session() as session:
            r = session.post(API_URL, json=payload, headers=HEADERS)
            r.raise_for_status()
            data = r.json()

        result = data.get("result", {})
        if not result.get("success"):
            raise Exception(f"API call unsuccessful: {result!r}")

        entries: list[Collection] = []
        for bin_type, label in TYPE_LABELS.items():
            key = f"next{bin_type.capitalize()}Date"
            # Prefer the ISO date; fall back to parsing the display string
            date = self._parse_iso_date(result.get(key))
            if date is None:
                date = self._parse_display_date(result.get(f"{key}Display") or "")
            if date is None:
                continue
            entries.append(
                Collection(
                    date=date,
                    t=label,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
