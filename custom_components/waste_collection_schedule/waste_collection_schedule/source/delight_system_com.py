import datetime
import re
import unicodedata

import requests
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
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
    "Shinjuku Okubo 1 chome (town / chome)": {
        "municipality": "shinjukuku",
        "area_name": "Okubo / 1 chome",
        "language_code": "en",
    },
    "Osaka Kita ward Ukita 1-chome 2-ban 2-5 go (ward / chome / ban / go)": {
        "municipality": "大阪市",
        "area_name": "北区 / 浮田1丁目 / 2番 / 2～5号",
        "language_code": "ja",
    },
}

# Path segment is lowercase "threeR" as required by the live API.
API_BASE = "https://threer1.delight-system.com/threeR/api"
# Sent on every request; bump when the upstream app version changes.
APP_VERSION = "a2.10.1"

# Deepest level area/areaList accepts (parent names go in area_name1 to area_name3).
_MAX_AREA_LEVEL = 4
# Levels the old leaf-name lookup walks; kept so existing configs resolve as before.
_LEAF_NAME_LEVELS = 3
AREA_PATH_SEPARATOR = " / "

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
        "Where the app asks for several levels, enter all of them, separated by "
        "` / ` (e.g. `Okubo / 1 chome`). "
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
        "area_name": (
            "Area from the app, e.g. `Aizumi-cho`. Where the app asks for several "
            "levels, give every level, e.g. `Okubo / 1 chome`."
        ),
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


def _match_key(value: str) -> str:
    # Fold full-width characters and case, and collapse runs of spaces.
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _join_path(path: tuple[str, ...]) -> str:
    return AREA_PATH_SEPARATOR.join(path)


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
    area_name3: str = "",
) -> list[dict]:
    # Fetch one level of the area tree (levels 1 to 4, parent names in area_name*).
    result = _api_get(
        session,
        "area/areaList",
        {
            "jichitai_id": jichitai_id,
            "area_level": str(area_level),
            "area_name1": area_name1,
            "area_name2": area_name2,
            "area_name3": area_name3,
            "language_code": language_code,
            "user_id": "",
        },
    )
    return result.get("area_info_array") or []


class _AreaTree:
    # Area tree of one municipality, fetched lazily; each list is fetched once.

    def __init__(
        self, session: requests.Session, jichitai_id: str, language_code: str
    ) -> None:
        self._session = session
        self._jichitai_id = jichitai_id
        self._language_code = language_code
        self._children: dict[tuple[str, ...], list[tuple[str, str | None]]] = {}

    def children(self, path: tuple[str, ...]) -> list[tuple[str, str | None]]:
        # (name, area_id) of the nodes below path; area_id is None for inner nodes.
        if len(path) >= _MAX_AREA_LEVEL:
            return []
        if path not in self._children:
            parents = list(path) + [""] * (_MAX_AREA_LEVEL - 1 - len(path))
            areas = _fetch_area_list(
                self._session,
                self._jichitai_id,
                self._language_code,
                len(path) + 1,
                *parents,
            )
            self._children[path] = [
                (
                    area.get("area_name") or "",
                    str(area["area_id"]) if area.get("area_id") else None,
                )
                for area in areas
            ]
        return self._children[path]


def _match_path(
    tree: _AreaTree, parent: tuple[str, ...], remaining: str
) -> list[tuple[tuple[str, ...], str | None]]:
    # Every node below parent whose path spells out remaining, with or without
    # separators between the levels. Only branches whose name starts the
    # remaining input are fetched.
    remaining = remaining.lstrip(" /")
    matches = []
    for name, area_id in tree.children(parent):
        key = _match_key(name)
        if not key or not remaining.startswith(key):
            continue
        path = (*parent, name)
        rest = remaining[len(key) :].lstrip(" /")
        if not rest:
            matches.append((path, area_id))
        elif area_id is None:
            matches.extend(_match_path(tree, path, rest))
    return matches


def _collect_areas(
    tree: _AreaTree, parent: tuple[str, ...] = ()
) -> list[tuple[tuple[str, ...], str]]:
    # Every (path, area_id) down to level 3, as the old leaf-name lookup saw them.
    result = []
    for name, area_id in tree.children(parent):
        path = (*parent, name)
        if area_id:
            result.append((path, area_id))
        elif len(path) < _LEAF_NAME_LEVELS:
            result.extend(_collect_areas(tree, path))
    return result


def _resolve_leaf_name(tree: _AreaTree, area_name: str) -> str:
    # Old lookup by the last level's name alone (exact, then substring), kept for
    # configs made before full paths were accepted. Repeated names are rejected
    # instead of taking the first one, which is often the wrong area.
    target = _normalize(area_name)
    areas = _collect_areas(tree)

    matches = [
        (path, area_id) for path, area_id in areas if _normalize(path[-1]) == target
    ]
    if not matches:
        matches = [
            (path, area_id) for path, area_id in areas if target in _normalize(path[-1])
        ]
    if len(matches) == 1:
        return matches[0][1]

    if matches:
        raise SourceArgAmbiguousWithSuggestions(
            "area_name", area_name, [_join_path(path) for path, _ in matches]
        )
    suggestions = [name for name, _ in tree.children(())]
    raise SourceArgumentNotFoundWithSuggestions("area_name", area_name, suggestions)


def _resolve_area_id(
    session: requests.Session,
    jichitai_id: str,
    area_name: str,
    language_code: str,
) -> str:
    # Map an area path such as "Okubo / 1 chome" to area_id, one level at a time.
    # The separators are optional, and the top level may be left out.
    tree = _AreaTree(session, jichitai_id, language_code)
    target = _match_key(area_name)

    matches = _match_path(tree, (), target)
    if not matches:
        for name, area_id in tree.children(()):
            if area_id is None:
                matches.extend(_match_path(tree, (name,), target))

    if len(matches) == 1 and matches[0][1]:
        return matches[0][1]
    if matches:
        # Several areas fit, or the input stops above a collection area, which
        # gets the next level down as suggestions.
        suggestions = []
        for path, area_id in matches:
            if area_id:
                suggestions.append(_join_path(path))
            else:
                suggestions.extend(
                    _join_path((*path, name)) for name, _ in tree.children(path)
                )
        raise SourceArgAmbiguousWithSuggestions("area_name", area_name, suggestions)

    return _resolve_leaf_name(tree, area_name)


def _icon_for_trash_kind(name: str) -> str | None:
    # Best-effort icon from English or Japanese waste-type labels.
    lower = name.lower()
    if "plastic bottle" in lower or "ペットボトル" in name:
        return Icons.PLASTIC_PET
    if "recyclable" in lower or "資源" in name:
        return Icons.RECYCLING
    if "non-combustible" in lower or "不燃" in name:
        return Icons.NON_COMBUSTIBLE
    if "combustible" in lower or "可燃" in name:
        return Icons.COMBUSTIBLE
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
            # It lists the top level; picking an inner node offers the next level.
            tree = _AreaTree(self._session, jichitai_id, self._language_code)
            suggestions = [name for name, _ in tree.children(())]
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
            ) from None
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
