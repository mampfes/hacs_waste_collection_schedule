import datetime
import re

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "ThreeR"
DESCRIPTION = (
    "Source for Japanese municipalities using the ThreeR garbage collection app."
)
URL = "https://threer1.delight-system.com"
COUNTRY = "jp"

LANGUAGE_CODES = ["en", "ja", "ko"]

TEST_CASES = {
    "Shinjuku Aizumi-cho (by municipality id)": {
        "municipality": "shinjukuku",
        "area_name": "Aizumi-cho",
        "language_code": "en",
    },
    "Shinjuku Aizumi-cho (by municipality name)": {
        "municipality": "Shinjuku City",
        "area_name": "Aizumi-cho",
        "language_code": "en",
    },
}

# Path segment is lowercase "threeR" as required by the live API.
API_BASE = "https://threer1.delight-system.com/threeR/api"
# Sent on every request; bump when the upstream app version changes.
APP_VERSION = "a2.10.1"

# Trash kinds that mark non-collection days rather than actual pickups.
_SKIP_NAME_PATTERNS = re.compile(
    r"(no collection|not collected|収集はありません|large-sized|"
    r"items not collected|home appliances recycling)",
    re.IGNORECASE,
)

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your municipality and neighbourhood exactly as shown in the ThreeR "
        "garbage app (e.g. municipality `Shinjuku City`, area `Aizumi-cho`). "
        "If a value is not recognised, the setup form will offer matching options "
        "from the live API."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "area_name": "Area name",
        "language_code": "Language",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": (
            "Municipality name or ID from the ThreeR app, e.g. `Shinjuku City` "
            "or `shinjukuku`."
        ),
        "area_name": ("Neighbourhood/chōme name from the app, e.g. `Aizumi-cho`."),
        "language_code": (
            "Language for municipality, area, and waste type labels from the API."
        ),
    },
}

CONFIG_FLOW_TYPES = {
    "language_code": {
        "type": "SELECT",
        "values": LANGUAGE_CODES,
    },
}


def _normalize(value: str) -> str:
    # Strip and case-fold for case-insensitive user input matching.
    return value.strip().casefold()


def _api_get(session: requests.Session, path: str, params: dict) -> dict:
    # GET an API endpoint and return rest_result, or raise on HTTP/API errors.
    response = session.get(
        f"{API_BASE}/{path}",
        params={"app_version": APP_VERSION, **params},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    # ThreeR wraps payloads in rest_error_kbn / rest_result (typo: rest_error_massage).
    if payload.get("rest_error_kbn") != "0":
        message = payload.get("rest_error_massage") or "Unknown API error"
        raise requests.HTTPError(message)
    return payload["rest_result"]


def _get_all_municipalities(
    session: requests.Session, language_code: str
) -> list[tuple[str, str]]:
    # Return (jichitai_id, jichitai_name) for every municipality on the platform.
    result = []
    prefectures = _api_get(
        session,
        "todofuken/getList",
        {"language_code": language_code, "user_id": ""},
    )["todofuken_info_array"]

    for prefecture in prefectures:
        code = str(prefecture["todofuken_code"]).strip()
        municipalities = _api_get(
            session,
            "jichitai/getList",
            {
                "todofuken_code": code,
                "language_code": language_code,
                "user_id": "",
            },
        )["jichitai_info_array"]
        for entry in municipalities:
            result.append((entry["jichitai_id"], entry["jichitai_name"]))
    return result


def _resolve_municipality(
    session: requests.Session, municipality: str, language_code: str
) -> str:
    # Map user input to jichitai_id (accepts ID or display name).
    target = _normalize(municipality)
    all_municipalities = _get_all_municipalities(session, language_code)

    # Exact match on API id or localised name.
    for jichitai_id, jichitai_name in all_municipalities:
        if _normalize(jichitai_id) == target or _normalize(jichitai_name) == target:
            return jichitai_id

    # Fall back to a unique substring match.
    matches = []
    for jichitai_id, jichitai_name in all_municipalities:
        name = _normalize(jichitai_name)
        if target in name or target in _normalize(jichitai_id):
            matches.append(jichitai_id)

    if len(matches) == 1:
        return matches[0]

    suggestions = []
    for _, jichitai_name in all_municipalities:
        suggestions.append(jichitai_name)
    suggestions.sort()
    raise SourceArgumentNotFoundWithSuggestions(
        "municipality", municipality, suggestions
    )


def _fetch_area_list(
    session: requests.Session,
    jichitai_id: str,
    language_code: str,
    area_level: int,
    area_name1: str = "",
    area_name2: str = "",
) -> list[dict]:
    # Fetch one level of the area tree (levels 1–3, parent names in area_name*).
    result = _api_get(
        session,
        "area/areaList",
        {
            "jichitai_id": jichitai_id,
            "area_level": str(area_level),
            "area_name1": area_name1,
            "area_name2": area_name2,
            "area_name3": "",
            "language_code": language_code,
            "user_id": "",
        },
    )
    return result.get("area_info_array") or []


def _collect_areas(
    session: requests.Session,
    jichitai_id: str,
    language_code: str,
    area_level: int = 1,
    area_name1: str = "",
    area_name2: str = "",
) -> list[tuple[str, str]]:
    # Return every selectable (area_name, area_id) pair for a municipality.
    result = []
    areas = _fetch_area_list(
        session, jichitai_id, language_code, area_level, area_name1, area_name2
    )

    for area in areas:
        name = area.get("area_name") or ""
        area_id = area.get("area_id")
        if area_id:
            result.append((name, str(area_id)))
            continue

        # Intermediate nodes have no area_id; recurse into child levels.
        if area_level == 1:
            children = _collect_areas(session, jichitai_id, language_code, 2, name, "")
            result.extend(children)
        elif area_level == 2:
            children = _collect_areas(
                session, jichitai_id, language_code, 3, area_name1, name
            )
            result.extend(children)

    return result


def _resolve_area_id(
    session: requests.Session,
    jichitai_id: str,
    area_name: str,
    language_code: str,
) -> str:
    # Map neighbourhood name to area_id (same exact-then-substring logic as municipality).
    target = _normalize(area_name)
    areas = _collect_areas(session, jichitai_id, language_code)

    for name, area_id in areas:
        if _normalize(name) == target:
            return area_id

    matches = []
    for name, area_id in areas:
        if target in _normalize(name):
            matches.append(area_id)

    if len(matches) == 1:
        return matches[0]

    suggestions = []
    for name, _ in areas:
        suggestions.append(name)
    suggestions.sort()
    raise SourceArgumentNotFoundWithSuggestions("area_name", area_name, suggestions)


def _icon_for_trash_kind(name: str) -> str | None:
    # Best-effort icon from English or Japanese waste-type labels.
    lower = name.lower()
    if "plastic bottle" in lower or "ペットボトル" in name:
        return Icons.PLASTIC_PACKAGING
    if "recyclable" in lower or "資源" in name:
        return Icons.RECYCLING
    if "non-combustible" in lower or "不燃" in name:
        return Icons.GENERAL_WASTE
    if "combustible" in lower or "可燃" in name:
        return Icons.GENERAL_WASTE
    if "organic" in lower or "生ごみ" in name:
        return Icons.BIO_KITCHEN
    if "paper" in lower or "紙" in name:
        return Icons.PAPER
    if "glass" in lower or "ガラス" in name:
        return Icons.GLASS
    return None


class Source:
    def __init__(
        self,
        language_code: str,
        municipality: str = "",
        area_name: str = "",
    ) -> None:
        self._session = requests.Session()

        language_code = language_code.strip()
        if not language_code:
            raise SourceArgumentRequiredWithSuggestions(
                "language_code",
                "Select the language for municipality, area, and waste type labels.",
                LANGUAGE_CODES,
            )
        if language_code not in LANGUAGE_CODES:
            raise SourceArgumentNotFoundWithSuggestions(
                "language_code", language_code, LANGUAGE_CODES
            )
        self._language_code = language_code

        municipality = municipality.strip()
        area_name = area_name.strip()
        if not municipality:
            raise SourceArgumentRequired(
                "municipality",
                "Enter the municipality from the ThreeR app, e.g. Shinjuku City.",
            )

        jichitai_id = _resolve_municipality(
            self._session, municipality, self._language_code
        )

        if not area_name:
            # Empty area_name triggers the config-flow dropdown (RSAG-style wizard).
            areas = _collect_areas(self._session, jichitai_id, self._language_code)
            suggestions = []
            for name, _ in areas:
                suggestions.append(name)
            suggestions.sort()
            raise SourceArgumentRequiredWithSuggestions(
                "area_name",
                "Select your collection area as shown in the ThreeR app.",
                suggestions,
            )

        self._area_id = _resolve_area_id(
            self._session, jichitai_id, area_name, self._language_code
        )
        self._area_name = area_name

    def fetch(self) -> list[Collection]:
        # API requires a user_id tied to the collection area before returning data.
        user_id = self._register_user()
        data = self._get_calendar_data(user_id)

        trash_kinds = {}
        for item in data.get("trash_kind_array", []):
            trash_kinds[item["trash_kind_id"]] = item["trash_kind_name"]

        entries = []
        for event in data.get("calendar_array", []):
            kind_id = event.get("trash_kind_id")
            kind_name = trash_kinds.get(kind_id)
            if not kind_name or _SKIP_NAME_PATTERNS.search(kind_name):
                continue

            date = datetime.date(
                int(event["year"]),
                int(event["month"]),
                int(event["day"]),
            )
            entries.append(
                Collection(date, kind_name, icon=_icon_for_trash_kind(kind_name))
            )

        return entries

    def _register_user(self) -> str:
        # Create a throwaway user for this area (mirrors first launch of the app).
        try:
            result = _api_get(
                self._session,
                "user/regist",
                {
                    "user_id": "",  # empty → API allocates a new user_id
                    "area_id": self._area_id,
                    "language_code": self._language_code,
                },
            )
        except requests.HTTPError:
            raise SourceArgumentNotFound(
                "area_name",
                self._area_name,
                "The API rejected this collection area. Check your municipality "
                "and area name match the ThreeR app.",
            )
        return result["user_id"]

    def _get_calendar_data(self, user_id: str) -> dict:
        # Feature flags mirror the app; only calendar_flag=1 is needed here.
        return _api_get(
            self._session,
            "allData/getData",
            {
                "user_id": user_id,
                "jichitai_setting_flag": "0",
                "jichitai_info_flag": "0",
                "quiz_flag": "0",
                "bunbetsu_flag": "0",
                "benricho_flag": "0",
                "calendar_flag": "1",
                "app_info_flag": "0",
            },
        )
