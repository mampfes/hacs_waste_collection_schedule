from datetime import date, datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Saver"
DESCRIPTION = (
    "Source for Saver waste collection in West-Brabant (Roosendaal, "
    "Halderberge, Bergen op Zoom, Rucphen, Zundert, Steenbergen, Woensdrecht)."
)
URL = "https://saver.nl"
COUNTRY = "nl"

TEST_CASES = {
    "Roosendaal Eikenlaan 1": {"postcode": "4702AA", "huisnummer": 1},
    "Oudenbosch Voorzet 1": {"postcode": "4731XR", "huisnummer": "1"},
    "St. Willebrord Weberstraat 1": {"postcode": "4711AA", "huisnummer": 1},
}

ICON_MAP = {
    "GFT": "mdi:leaf",
    "Restafval": "mdi:trash-can",
    "PBD": "mdi:recycle",
    "PMD": "mdi:recycle",
    "Plastic": "mdi:recycle",
    "Papier": "mdi:paper-roll",
    "Glas": "mdi:bottle-soda",
    "Textiel": "mdi:hanger",
    "Kerstboom": "mdi:pine-tree",
    "Snoeiafval": "mdi:tree",
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Dutch postal code (4 digits + 2 letters), e.g. 4702AA",
        "huisnummer": "House number",
        "toevoeging": "House letter or addition (only required when more than one address shares the postcode/huisnummer)",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postal code",
        "huisnummer": "House number",
        "toevoeging": "Addition",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Use the same postcode and house number you would enter at "
        "https://saver.nl/afvalkalender. If your address has a letter or "
        "addition (e.g. '5a'), provide the letter/addition in the "
        "'toevoeging' argument."
    ),
}

API_BASE = "https://saver.nl"


class Source:
    def __init__(self, postcode: str, huisnummer, toevoeging: str = ""):
        self._postcode = str(postcode).replace(" ", "").upper()
        self._huisnummer = str(huisnummer).strip()
        self._toevoeging = str(toevoeging or "").strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})

        bagid = self._resolve_bagid(session)
        stream_titles = self._get_stream_titles(session, bagid)

        today = date.today()
        years = [today.year]
        if today.month >= 11:
            years.append(today.year + 1)

        entries: list[Collection] = []
        for year in years:
            r = session.get(
                f"{API_BASE}/rest/adressen/{bagid}/kalender/{year}", timeout=30
            )
            r.raise_for_status()
            for item in r.json():
                stream_id = item.get("afvalstroom_id")
                date_str = item.get("ophaaldatum")
                if not stream_id or not date_str:
                    continue
                collection_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                title = stream_titles.get(stream_id, f"Stream {stream_id}")
                entries.append(
                    Collection(
                        date=collection_date,
                        t=title,
                        icon=self._icon_for(title),
                    )
                )

        return entries

    def _resolve_bagid(self, session: requests.Session) -> str:
        r = session.get(
            f"{API_BASE}/adressen/{self._postcode}:{self._huisnummer}", timeout=30
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            raise SourceArgumentNotFound("postcode", self._postcode)

        if len(data) == 1 and not self._toevoeging:
            return data[0]["bagid"]

        target = self._toevoeging.casefold()
        for entry in data:
            suffix = (
                (entry.get("huisletter", "") or "")
                + (entry.get("toevoeging", "") or "")
            ).casefold()
            if suffix == target:
                return entry["bagid"]

        suggestions = [
            (
                f"{entry.get('huisletter', '')}{entry.get('toevoeging', '')}".strip()
                or "(none)"
            )
            for entry in data
        ]
        raise SourceArgumentNotFoundWithSuggestions(
            "toevoeging", self._toevoeging, suggestions
        )

    @staticmethod
    def _get_stream_titles(session: requests.Session, bagid: str) -> dict[int, str]:
        r = session.get(f"{API_BASE}/rest/adressen/{bagid}/afvalstromen", timeout=30)
        r.raise_for_status()
        result: dict[int, str] = {}
        for item in r.json():
            stream_id = item.get("id")
            if stream_id is None:
                continue
            title = item.get("menu_title") or item.get("title") or ""
            if title:
                result[stream_id] = title.strip()
        return result

    @staticmethod
    def _icon_for(waste_type: str) -> str | None:
        lowered = waste_type.casefold()
        for key, icon in ICON_MAP.items():
            if key.casefold() in lowered:
                return icon
        return None
