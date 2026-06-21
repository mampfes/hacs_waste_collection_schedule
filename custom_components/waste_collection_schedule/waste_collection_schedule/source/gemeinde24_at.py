from typing import Any, TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dependent_select
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    ELECTRONICS,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Demonstrates: the config_params.dependent_select(parent, child) PARAM and the
# get_choices() contract it relies on, on the BaseSource pipeline.
#
# Gemeinde24 is a cascading provider: the user first chooses a municipality
# (Gemeinde), then a street/local area (Strasse) whose option list is valid only
# within that municipality. The street list is fetched LIVE per municipality, so
# this is the textbook two-level dependent_select cascade.
#
# dependent_select("gemeinde", "strasse") declares that pairing. The framework
# collects the parent value, then calls Source.get_choices(parent_value) to
# populate the child selector. get_choices() here resolves the municipality name
# to its GemeindeID and fetches that municipality's streets from wastesetup_v2.

API_BASE_URL = "https://www.gemeinde24.at/admin/API"
API_KEY = "justanapp"
APP_VERSION = "20251020"
# gemeinden.php sorts by distance from a coordinate but returns every
# municipality, so a fixed central-Austria point yields the full list.
SEARCH_LATITUDE = "47.5000"
SEARCH_LONGITUDE = "14.5000"

# Map the gemeinde24 wasteID code to a canonical WasteType. The human title is
# also resolved against the shared German vocabulary; the code map is the
# authoritative override (titles are free text and occasionally custom).
_CODE_MAP = {
    "rm": GENERAL_WASTE,
    "bm": ORGANIC,
    "lf": RECYCLABLES,
    "ap": PAPER,
    "ag": GLASS,
    "am": ELECTRONICS,
    "sp": BULKY_WASTE,
    "gs": GARDEN_WASTE,
    "ps": HAZARDOUS,
    "el": ELECTRONICS,
}


class _WasteItem(TypedDict):
    """The fields read from each waste_list.php entry."""

    datum: str
    title: str
    wasteID: str


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _normalize(value: str) -> str:
    normalized = value.casefold().strip()
    normalized = (
        normalized.replace("ß", "ss")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
    )
    normalized = normalized.replace("-", " ")
    return " ".join(normalized.split())


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _suggestions(value: str, candidates: list[str]) -> list[str]:
    unique = _deduplicate(candidates)
    query = _normalize(value)
    if not unique:
        return []
    starts = [c for c in unique if _normalize(c).startswith(query)]
    contains = [c for c in unique if query and query in _normalize(c)]
    return _deduplicate(starts + contains + unique)[:20]


def _gemeinden(session) -> list[dict]:
    """Fetch the full municipality list (live)."""
    resp = session.post(
        f"{API_BASE_URL}/gemeinden.php",
        params={"apiKEY": API_KEY},
        data={"lat": SEARCH_LATITUDE, "long": SEARCH_LONGITUDE, "apiKEY": API_KEY},
        timeout=30,
    )
    payload = resp.json()
    if str(payload.get("code", "")).upper() != "OK":
        raise SourceArgumentNotFoundWithSuggestions("gemeinde", "", [])
    reports = payload.get("reports")
    return (
        [r for r in reports if isinstance(r, dict)] if isinstance(reports, list) else []
    )


def _resolve_gemeinde_id(session, gemeinde: str) -> str:
    """Resolve a municipality name to its GemeindeID (live)."""
    if not gemeinde:
        raise SourceArgumentRequired(
            "gemeinde", "or provide 'gemeinde_id' as an alternative."
        )
    reports = _gemeinden(session)
    all_names = [_clean(r.get("Gemeindename")) for r in reports if r.get("GemeindeID")]
    matches = [
        (
            _clean(r.get("GemeindeID")),
            _clean(r.get("Gemeindename")),
            _clean(r.get("zip")),
        )
        for r in reports
        if _clean(r.get("GemeindeID"))
        and _normalize(_clean(r.get("Gemeindename"))) == _normalize(gemeinde)
    ]
    if len(matches) == 1:
        return matches[0][0]
    if len(matches) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "gemeinde",
            gemeinde,
            _deduplicate(
                [f"{name} ({zip_}, GemeindeID={gid})" for gid, name, zip_ in matches]
            ),
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "gemeinde", gemeinde, _suggestions(gemeinde, all_names)
    )


def _streets(session, gemeinde_id: str) -> list[tuple[str, str]]:
    """Fetch (street name, streetID) pairs for a municipality (live)."""
    resp = session.get(
        f"{API_BASE_URL}/wastesetup_v2.php",
        params={"GemeindeID": gemeinde_id, "apiKEY": API_KEY},
        timeout=30,
    )
    payload = resp.json()
    if str(payload.get("code", "")).upper() != "OK":
        raise SourceArgumentNotFoundWithSuggestions("strasse", "", [])
    streets = payload.get("strassen")
    if not isinstance(streets, list):
        return []
    pairs = []
    for street in streets:
        if not isinstance(street, dict):
            continue
        name = _clean(street.get("street"))
        sid = _clean(street.get("streetID"))
        if name and sid:
            pairs.append((name, sid))
    return pairs


def _resolve_street_id(session, gemeinde_id: str, strasse: str, street_id: str) -> str:
    """Resolve a street name (or validate a street_id) within a municipality."""
    pairs = _streets(session, gemeinde_id)
    if street_id:
        if any(sid == street_id for _, sid in pairs):
            return street_id
        raise SourceArgumentNotFoundWithSuggestions(
            "street_id",
            street_id,
            [f"{name} (streetID={sid})" for name, sid in pairs],
        )
    if not strasse:
        raise SourceArgumentRequired(
            "strasse", "or provide 'street_id' as an alternative."
        )
    matches = [(n, s) for n, s in pairs if _normalize(n) == _normalize(strasse)]
    if len(matches) == 1:
        return matches[0][1]
    if len(matches) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "strasse",
            strasse,
            [f"{name} (streetID={sid})" for name, sid in matches],
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "strasse", strasse, _suggestions(strasse, [n for n, _ in pairs])
    )


@final
class Source(BaseSource):
    TITLE = "Gemeinde24"
    DESCRIPTION = "Source for Gemeinde24 municipal app waste collection data."
    URL = "https://www.gemeinde24.at"
    COUNTRY = "at"
    CODEOWNERS = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Gaal": {"gemeinde": "Gaal", "strasse": "Gaal"},
    }

    PARAMS = [dependent_select("gemeinde", "strasse", child_label="Street")]

    HOWTO = {
        "en": (
            "Choose your municipality (Gemeinde), then choose your street/local "
            "area (Strasse) from the list that loads for that municipality."
        ),
        "de": (
            "Wählen Sie Ihre Gemeinde, dann Ihre Straße/Ihren Ortsteil aus der "
            "Liste, die für diese Gemeinde geladen wird."
        ),
    }

    parse = parsers.JsonParser("waste_list.php", shape=list[_WasteItem])

    transformer = JsonTransformer(
        date_key="_date",
        type_key="title",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
    )

    def __init__(self, gemeinde: str | None = None, strasse: str | None = None):
        # validate() (in super) enforces the required gemeinde + strasse cascade.
        super().__init__(gemeinde=gemeinde, strasse=strasse)
        self._gemeinde = _clean(gemeinde)
        self._strasse = _clean(strasse)

    @classmethod
    def get_parent_choices(cls) -> list[str]:
        """Return the full list of municipality (Gemeinde) names.

        Implements the optional parent half of the dependent_select contract:
        the framework calls this to populate the parent (Gemeinde) selector.
        gemeinden.php returns every municipality (sorted by distance from a
        fixed point), so this is the complete option list.
        """
        from curl_cffi import requests as _cffi

        session = _cffi.Session(impersonate="chrome")
        names = [_clean(r.get("Gemeindename")) for r in _gemeinden(session)]
        return _deduplicate(sorted(n for n in names if n))

    @classmethod
    def get_choices(cls, parent_value: str) -> list[str]:
        """Return the street names available within a municipality.

        Implements the config_params.dependent_select() contract: the framework
        calls this with the chosen parent (Gemeinde) value to populate the child
        (Strasse) selector. Resolves the municipality name to its GemeindeID,
        then fetches that municipality's streets live.
        """
        from curl_cffi import requests as _cffi

        session = _cffi.Session(impersonate="chrome")
        gemeinde_id = _resolve_gemeinde_id(session, _clean(parent_value))
        return _deduplicate([name for name, _ in _streets(session, gemeinde_id)])

    def retrieve(self, source):
        gemeinde_id = _resolve_gemeinde_id(source.session, self._gemeinde)
        street_id = _resolve_street_id(source.session, gemeinde_id, self._strasse, "")
        return source.session.get(
            f"{API_BASE_URL}/content2.php",
            params={
                "GemeindeID": gemeinde_id,
                "apiKEY": API_KEY,
                "StreetID": street_id,
                "appversion": APP_VERSION,
            },
            timeout=30,
        )

    def preprocessor(self, records, source=None):
        """Split the gemeinde24 'weekday-YYYY-MM-DD' date into a clean field.

        Each record's ``datum`` looks like ``Do-2026-07-02`` (German weekday
        prefix). The transformer's ``date_key`` reads the cleaned ``_date`` this
        adds (``2026-07-02``); records whose date can't be split are dropped, and
        the wasteID code is used to override the canonical type when known.
        """
        for record in records:
            if not isinstance(record, dict):
                continue
            _, sep, date_value = _clean(record.get("datum")).partition("-")
            if not sep or not date_value:
                continue
            title = _clean(record.get("title"))
            if not title:
                continue
            code = _clean(record.get("wasteID")).lower()
            # Let an explicit code mapping win over free-text title resolution by
            # rewriting the title to the canonical German name when we know it.
            mapped = _CODE_MAP.get(code)
            if mapped is not None:
                title = mapped.names["de"]
            yield {"_date": date_value, "title": title}
