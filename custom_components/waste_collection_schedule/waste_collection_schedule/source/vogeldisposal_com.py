import datetime
import logging

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

_LOGGER = logging.getLogger(__name__)

TITLE = "Vogel Disposal Service"
DESCRIPTION = (
    "Residential trash and recycling collection schedules for "
    "Vogel Disposal Service (Mars, PA)."
)
URL = "https://www.vogeldisposal.com/"
COUNTRY = "us"

TEST_CASES = {
    "Butler Twp 1002 Tudor Dr": {
        "municipality": "BUTLER TWP, BUTLER COUNTY",
        "address": "1002 TUDOR DR",
    },
}

ICON_MAP = {
    "Trash": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your municipality and street address. Exact spelling is not "
        "required: a rough municipality (for example 'butler twp') and a "
        "partial street address (for example '1002 tudor') are matched "
        "automatically. If the input matches more than one place, the matching "
        "options are shown so you can pick the right one."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "address": "Street address",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Your Vogel municipality, for example 'butler twp' or 'BUTLER TWP, BUTLER COUNTY'.",
        "address": "Your street address, for example '1002 tudor' or '1002 TUDOR DR'.",
    },
}

SOURCE_CODEOWNERS = ["@jcarr"]

API_BASE = "https://www.vogeldisposal.com"


class Source:
    _MONTHS = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    def __init__(self, municipality: str, address: str):
        self._municipality = municipality
        self._address = address

    def _session(self):
        return requests.Session(impersonate="chrome")

    def _post(self, session, path: str, payload: dict):
        resp = session.post(f"{API_BASE}/collectionlookup.aspx/{path}", json=payload)
        resp.raise_for_status()
        return resp.json().get("d")

    @staticmethod
    def _norm(value: str) -> str:
        return value.upper().replace(".", "").strip()

    def _resolve_municipality(self, session) -> str:
        # GetCities is a prefix search against canonical names like
        # "BUTLER TWP, BUTLER COUNTY", so reduce free-form input (e.g.
        # "butler township") to matching prefixes until something comes back.
        user = self._municipality.strip()
        words = user.split()
        queries = [
            user,
            user.split(",")[0].strip(),
            words[0] if words else "",
            user[:4],
        ]
        candidates: list[str] = []
        for query in queries:
            if not query:
                continue
            candidates = self._post(session, "GetCities", {"strInput": query}) or []
            if candidates:
                break
        for city in candidates:
            if self._norm(city).split(",")[0] == self._norm(user).split(",")[0]:
                return city
        if len(candidates) == 1:
            return candidates[0]
        raise SourceArgumentNotFoundWithSuggestions(
            "municipality", self._municipality, candidates
        )

    def _resolve_address(self, session, municipality: str) -> str:
        user = self._address.strip()
        suggestions = (
            self._post(
                session,
                "GetSuggestedAddresses",
                {"strAddress": user, "municipality": municipality},
            )
            or []
        )
        for address in suggestions:
            if self._norm(address) == self._norm(user):
                return address
        if len(suggestions) == 1:
            return suggestions[0]
        raise SourceArgumentNotFoundWithSuggestions(
            "address", self._address, suggestions
        )

    def _resolve(self, session) -> dict:
        # Resolve free-form input to the canonical municipality/address the
        # pickup endpoint expects (each raises a suggestion error if ambiguous).
        municipality = self._resolve_municipality(session)
        address = self._resolve_address(session, municipality)

        resp = session.post(
            f"{API_BASE}/collectionlookup.aspx/GetPickupInfoByAddress",
            json={"municipality": municipality, "strAddress": address},
        )
        info = resp.json().get("d") if resp.status_code == 200 else None
        if isinstance(info, dict) and info.get("success"):
            return info
        raise SourceArgumentNotFoundWithSuggestions("address", self._address, [])

    def _fetch_calendar(self, session, cd, rd, rw, year: int) -> str:
        resp = session.get(
            f"{API_BASE}/collectioncalendar.aspx",
            params={"rw": rw, "cd": cd, "rd": rd, "yr": year},
        )
        resp.raise_for_status()
        return resp.text

    def _parse(self, html: str) -> list[Collection]:
        soup = BeautifulSoup(html, "html.parser")
        entries: list[Collection] = []
        for grid in soup.select("table.monthTable"):
            title = grid.select_one(".calendarTitleBar")
            if title is None:
                continue
            parts = title.get_text(strip=True).split()
            month = self._MONTHS.get(parts[0].lower())
            if month is None:
                continue
            year = int(parts[-1])
            for cell in grid.select("td.pickupDay, td.recycleDay"):
                text = cell.get_text(strip=True)
                if not text.isdigit():
                    continue
                day = datetime.date(year, month, int(text))
                entries.append(Collection(day, "Trash", ICON_MAP["Trash"]))
                if "recycleDay" in cell.get("class", []):
                    entries.append(Collection(day, "Recycling", ICON_MAP["Recycling"]))
        return entries

    def fetch(self) -> list[Collection]:
        session = self._session()
        info = self._resolve(session)
        cd = info["weekdayNumber"]
        rd = info["recycleDayNumber"]
        rw = info["frequency"]

        this_year = datetime.date.today().year
        entries = self._parse(self._fetch_calendar(session, cd, rd, rw, this_year))
        if not entries:
            raise ValueError(
                "Vogel Disposal returned no collection dates for "
                f"{self._municipality!r} / {self._address!r}"
            )

        # Next year's calendar is published ahead of time; fetch it so the
        # schedule keeps rolling past December. It is best-effort: if it is not
        # yet available, keep the current-year schedule.
        try:
            entries += self._parse(
                self._fetch_calendar(session, cd, rd, rw, this_year + 1)
            )
        except Exception as err:
            _LOGGER.debug(
                "Vogel next-year (%s) calendar unavailable: %s",
                this_year + 1,
                err,
            )

        return entries
