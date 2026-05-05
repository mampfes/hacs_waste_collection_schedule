import json
import re
from datetime import datetime
from urllib.parse import quote, urlencode

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentException

TITLE = "Kauno švara"
DESCRIPTION = 'Source for UAB "Kauno švara".'
URL = "https://grafikai.svara.lt"
TEST_CASES = {
    "Demokratų g. 7, Kaunas": {
        "region": "Kauno m. sav.",
        "street": "Demokratų g.",
        "house_number": "7",
    },
    "Alytaus g. 2, Išlaužo k., Išlaužo sen. Prienų r. sav.": {
        "region": "Prienų r. sav.",
        "street": "Alytaus g.",
        "house_number": "2",
        "district": "Išlaužo sen.",
    },
}

ICON_MAP = {
    "mišrių atliekų": "mdi:trash-can",
    "antrinių žaliavų (popierius/plastikas)": "mdi:recycle",
    "antrinių žaliavų (stiklas)": "mdi:glass-fragile",
    "žaliųjų atliekų": "mdi:leaf",
}

# In late April 2026 grafikai.svara.lt was rewritten as a TanStack Start
# (TSR) React app. The previous REST endpoints (/api/contracts,
# /api/schedule) are gone — the new architecture proxies all data fetching
# through a single server function: GET /_serverFn/<sha256> with a Seroval-
# encoded payload of {data: {apiPath, tenantId}}.
#
# The function id is a sha256 baked into the JS bundle at build time and
# changes every time upstream rebuilds. We scrape the live JS bundles to
# find candidate ids and probe each against /schedule/getdistricts to pick
# the data-fetching one — no hardcoded id, no manual updates needed when
# upstream redeploys.
_BASE_URL = "https://grafikai.svara.lt"
_SERVER_FN_URL_TEMPLATE = _BASE_URL + "/_serverFn/{fn_id}"
_TENANT_ID = 1


def _seroval_encode_request(api_path: str, tenant_id: int = _TENANT_ID) -> str:
    """Encode a {data: {apiPath, tenantId}} payload as Seroval JSON.

    The full Seroval format is rich (handles cycles, refs, dates, regex, etc.),
    but the request payload here is tiny and acyclic — just two scalars wrapped
    in two object levels. We can hand-encode it directly without pulling in a
    Seroval library.
    """
    return json.dumps(
        {
            "t": {
                "t": 10,
                "i": 0,
                "p": {
                    "k": ["data"],
                    "v": [
                        {
                            "t": 10,
                            "i": 1,
                            "p": {
                                "k": ["apiPath", "tenantId"],
                                "v": [
                                    {"t": 1, "s": api_path},
                                    {"t": 2, "s": tenant_id},
                                ],
                            },
                            "o": 0,
                        }
                    ],
                },
                "o": 0,
            },
            "f": 63,
            "m": [],
        },
        separators=(",", ":"),
    )


def _seroval_decode(node):
    """Decode a Seroval-encoded value tree to a Python value.

    Handles the small subset of Seroval node types this API actually returns:
        t=0 number, t=1 string, t=2 bigint (we coerce to int),
        t=9 array, t=10/t=11 plain object.
    """
    if not isinstance(node, dict):
        return node
    t = node.get("t")
    if t == 0:
        return node.get("s")
    if t == 1:
        return node.get("s")
    if t == 2:
        return node.get("s")
    if t == 9:
        return [_seroval_decode(item) for item in node.get("a", [])]
    if t in (10, 11):
        p = node.get("p") or {}
        keys = p.get("k", [])
        vals = p.get("v", [])
        return {k: _seroval_decode(v) for k, v in zip(keys, vals)}
    return None


def _probe_data_fetcher(session: requests.Session, fn_id: str) -> bool:
    """Return True if `fn_id` is the data-fetching server function.

    Probes by calling /schedule/getdistricts (the cheapest known-safe API
    path on the upstream backend) and checking whether the decoded response
    has a `result` field whose value is a list (the shape the data fetcher
    returns for that endpoint). Other server functions either 4xx, return a
    Seroval error, or return a different shape.
    """
    payload = _seroval_encode_request("/schedule/getdistricts?search=")
    try:
        r = session.get(
            _SERVER_FN_URL_TEMPLATE.format(fn_id=fn_id) + "?payload=" + quote(payload),
            headers={
                "Accept": "application/json",
                "x-tsr-serverFn": "true",
            },
            timeout=8,
        )
    except requests.RequestException:
        return False
    if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
        return False
    try:
        decoded = _seroval_decode(r.json())
    except (ValueError, TypeError):
        return False
    return isinstance(decoded, dict) and isinstance(decoded.get("result"), list)


def _candidate_fn_ids(session: requests.Session) -> list[str]:
    """Scrape the live page and JS bundles for sha256-shaped server-fn ids.

    Returns deduplicated candidates in the order they appear in the bundle,
    or an empty list if scraping fails.
    """
    try:
        html = session.get(_BASE_URL + "/", timeout=15).text
    except requests.RequestException:
        return []
    bundles = re.findall(r"/assets/[A-Za-z0-9._-]+\.js", html)
    seen: set[str] = set()
    ordered: list[str] = []
    for bundle in bundles:
        try:
            js = session.get(_BASE_URL + bundle, timeout=15).text
        except requests.RequestException:
            continue
        # 64-char hex strings used as quoted string literals (the form
        # `createServerFn` registers them in) — narrower than matching every
        # hex blob, but agnostic to the minified factory's mangled name.
        for fn_id in re.findall(r'[\'"`]([0-9a-f]{64})[\'"`]', js):
            if fn_id not in seen:
                seen.add(fn_id)
                ordered.append(fn_id)
    return ordered


def _resolve_server_fn_id(session: requests.Session) -> str | None:
    """Discover the data-fetching server-function id from the live JS bundle.

    Returns None if discovery fails — the caller raises a descriptive error
    rather than silently using a stale hardcoded id.
    """
    for fn_id in _candidate_fn_ids(session):
        if _probe_data_fetcher(session, fn_id):
            return fn_id
    return None


class _StaleFnId(Exception):
    """Raised when a cached server-fn id stops responding correctly."""


class Source:
    def __init__(
        self,
        region: str,
        street: str,
        house_number: str,
        district: str | None = None,
        waste_object_ids: list[str | int] | None = None,
    ):
        if waste_object_ids is None:
            waste_object_ids = []
        if isinstance(waste_object_ids, (str, int)):
            waste_object_ids = [waste_object_ids]
        self._region = region
        self._street = street
        self._house_number = house_number
        self._district = district
        try:
            self._waste_object_ids = [
                int(x) for x in waste_object_ids if str(x).strip()
            ]
        except (ValueError, TypeError):
            raise SourceArgumentException(
                "waste_object_ids",
                "waste_object_ids must be a list of numeric values",
            )
        # Cached server-fn id, populated lazily on first fetch and
        # invalidated when an upstream redeploy makes the cached id stale.
        self._fn_id: str | None = None

    def _ensure_fn_id(self, session: requests.Session) -> str:
        if self._fn_id is None:
            self._fn_id = _resolve_server_fn_id(session)
        if self._fn_id is None:
            raise Exception(
                "Could not discover grafikai.svara.lt server-function id; "
                "site structure may have changed unexpectedly"
            )
        return self._fn_id

    def _raw_call(self, session: requests.Session, fn_id: str, api_path: str) -> dict:
        payload = _seroval_encode_request(api_path)
        r = session.get(
            _SERVER_FN_URL_TEMPLATE.format(fn_id=fn_id) + "?payload=" + quote(payload),
            headers={
                "Accept": "application/json, application/x-tss-framed, application/x-ndjson",
                "x-tsr-serverFn": "true",
            },
            timeout=20,
        )
        # Anything other than a normal JSON 200 implies the fn_id is no
        # longer valid (most likely upstream redeployed). Signal stale and
        # let the caller re-discover and retry once.
        if r.status_code != 200 or "json" not in r.headers.get("content-type", ""):
            raise _StaleFnId(f"fn_id {fn_id} returned HTTP {r.status_code}")
        decoded = _seroval_decode(r.json()) or {}
        if "result" not in decoded:
            raise _StaleFnId(
                f"fn_id {fn_id} returned unexpected shape: {r.text[:120]!r}"
            )
        return decoded

    def _call(self, session: requests.Session, api_path: str) -> dict:
        # On first call, discover. On a stale-id signal (e.g. upstream
        # redeployed since we cached the id), invalidate and re-discover
        # exactly once before failing.
        for attempt in range(2):
            fn_id = self._ensure_fn_id(session)
            try:
                return self._raw_call(session, fn_id, api_path)
            except _StaleFnId:
                self._fn_id = None
                if attempt == 1:
                    raise Exception(
                        f"grafikai.svara.lt rejected request to {api_path!r} "
                        "even after re-discovering the server-function id"
                    )
        raise AssertionError("unreachable")

    def fetch(self) -> list[Collection]:
        session = requests.Session()

        contracts_path = "/schedule/getcontracts?" + urlencode(
            {
                "address": self._street,
                "city": "",
                "houseNumber": self._house_number,
                "matchHouseNumber": "true",
                "pageIndex": 0,
                "pageSize": 50,
                "region": self._region,
                "subDistrict": self._district or "",
            }
        )
        contracts_resp = self._call(session, contracts_path)
        result = contracts_resp.get("result") or {}
        rows = result.get("data") or []

        entries: list[Collection] = []
        for row in rows:
            waste_object_id = row.get("wasteObjectId")
            if waste_object_id is None:
                continue
            if (
                self._waste_object_ids
                and int(waste_object_id) not in self._waste_object_ids
            ):
                continue
            description_plural = (row.get("descriptionPlural") or "").casefold()
            description_fmt = (row.get("descriptionFmt") or "").title()

            schedule_path = "/schedule/getschedule?" + urlencode(
                {
                    "address": "-",
                    "houseNumber": "-",
                    "pageIndex": 0,
                    "pageSize": 50,
                    "region": "-",
                    "subDistrict": "-",
                    "wasteObjectId": waste_object_id,
                }
            )
            schedule_resp = self._call(session, schedule_path)
            for d in schedule_resp.get("result") or []:
                date_str = d.get("dateFmt") or (d.get("date") or "")[:10]
                if not date_str:
                    continue
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
                entries.append(
                    Collection(
                        date=date,
                        t=description_fmt,
                        icon=ICON_MAP.get(description_plural),
                    )
                )

        return entries
