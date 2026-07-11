"""
AchieveForms (Firmstep) shared session and lookup helpers.

Many UK council waste-collection sources are built on the AchieveForms
(formerly Firmstep) self-service portal hosted at
``<council>-self.achieveservice.com``.  They all share the same two-step
handshake before data can be retrieved:

1. **Session initialisation** – obtain a ``sid`` (session key) by visiting
   the service landing page and calling ``authapi/isauthenticated``.
   An optional third GET to ``apibroker/domain/<hostname>`` warms the
   session on servers that require it.

2. **Lookup run** – POST to ``apibroker/runLookup`` with the ``sid`` and a
   ``formValues`` payload to retrieve the collection data.

Usage::

    import requests
    from waste_collection_schedule.service.AchieveForms import init_session, run_lookup

    session = requests.Session()
    sid = init_session(
        session,
        initial_url="https://council-self.achieveservice.com/en/service/Bin_days",
        auth_url="https://council-self.achieveservice.com/authapi/isauthenticated",
        hostname="council-self.achieveservice.com",
        auth_test_url="https://council-self.achieveservice.com/apibroker/domain/council-self.achieveservice.com",
    )
    result = run_lookup(
        session,
        api_url="https://council-self.achieveservice.com/apibroker/runLookup",
        sid=sid,
        lookup_id="<lookup_id>",
        form_values={"Section 1": {"UPRN": {"value": "100012345678"}}},
    )
"""

import json
import re
import time
from collections.abc import Callable, Hashable
from typing import TYPE_CHECKING, Any, TypeAlias

import requests

from waste_collection_schedule import preprocessors, response_shape
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def init_session(
    session: requests.Session,
    initial_url: str,
    auth_url: str,
    hostname: str,
    *,
    auth_test_url: str | None = None,
    timeout: int = 30,
    skip_landing_page: bool = False,
) -> str:
    """
    Perform the AchieveForms session handshake.

    Steps:
      1. GET ``initial_url`` (follows redirects; the final URL is passed as the
         ``uri`` parameter in the next step).
      2. GET ``auth_url`` with ``uri=<final_url>``, ``hostname=<hostname>``,
         ``withCredentials=true`` → extract ``r.json()["auth-session"]`` as
         the session key (sid).
      3. (Optional) GET ``auth_test_url`` with ``sid=<sid>`` and
         ``_=<timestamp_ms>`` to warm the session / perform a domain check.

    Parameters
    ----------
    session:
        A ``requests.Session`` that will be reused for subsequent API calls.
    initial_url:
        The service landing page URL.  The final URL after any redirects is
        used as the ``uri`` value when fetching the auth endpoint.
    auth_url:
        The ``authapi/isauthenticated`` endpoint URL.
    hostname:
        The AchieveForms hostname (e.g. ``council-self.achieveservice.com``).
    auth_test_url:
        Optional ``apibroker/domain/<hostname>`` URL.  When supplied, a GET
        is made after the auth call to warm the session.
    timeout:
        HTTP request timeout in seconds (default 30).
    skip_landing_page:
        When True, don't GET ``initial_url`` at all — use it verbatim as the
        ``uri`` value for the auth call. Some councils front the AchieveForms
        landing page itself with a bot-check that 403s a non-browser request,
        while the ``authapi`` endpoint accepts the same URL merely referenced
        as a query parameter (matching what a browser session would already
        have resolved it to). Default False preserves the original two-request
        behaviour for every existing caller.

    Returns
    -------
    str
        The session key (``auth-session`` value) to use in subsequent calls.

    Raises
    ------
    requests.HTTPError
        If any of the HTTP requests returns a non-2xx status code.
    """
    if skip_landing_page:
        uri = initial_url
    else:
        r = session.get(initial_url, timeout=timeout)
        r.raise_for_status()
        uri = r.url

    params: dict[str, str] = {
        "uri": uri,
        "hostname": hostname,
        "withCredentials": "true",
    }
    r = session.get(auth_url, params=params, timeout=timeout)
    r.raise_for_status()
    sid: str = r.json()["auth-session"]

    if auth_test_url is not None:
        params_test: dict[str, str | int] = {
            "sid": sid,
            "_": int(time.time() * 1000),
        }
        r = session.get(auth_test_url, params=params_test, timeout=timeout)
        r.raise_for_status()

    return sid


def run_lookup(
    session: requests.Session,
    api_url: str,
    sid: str,
    lookup_id: str,
    form_values: dict,
    *,
    timeout: int = 30,
    no_retry: str = "false",
    app_name: str = "AF-Renderer::Self",
    method: str = "POST",
    headers: "dict[str, str] | None" = None,
) -> dict:
    """
    Call ``apibroker/runLookup`` and return the parsed JSON response.

    Parameters
    ----------
    session:
        The ``requests.Session`` previously initialised with
        :func:`init_session`.
    api_url:
        The full ``apibroker/runLookup`` endpoint URL.
    sid:
        The session key obtained from :func:`init_session`.
    lookup_id:
        The AchieveForms lookup identifier (the ``id`` query-string parameter).
    form_values:
        The dictionary to nest under ``"formValues"`` in the JSON request body.
        Ignored when ``method="GET"`` (no body is sent).
    timeout:
        HTTP request timeout in seconds (default 30).
    no_retry:
        Value for the ``noRetry`` query-string parameter (default ``"false"``).
    app_name:
        Value for the ``app_name`` query-string parameter
        (default ``"AF-Renderer::Self"``).
    method:
        ``"POST"`` (default) sends ``form_values`` as the JSON body, the
        normal runLookup call. ``"GET"`` issues a bare GET against the same
        URL/query-params with no body, for a council whose flow fetches a
        token via a GET to the runLookup endpoint rather than a POST (see
        :class:`LookupStep`'s ``method`` argument).
    headers:
        Optional extra request headers for this call (e.g. a CSRF token a
        prior step obtained), merged over the session's defaults.

    Returns
    -------
    dict
        Parsed JSON response from the API.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returns a non-2xx status code.
    """
    params: dict[str, str | int] = {
        "id": lookup_id,
        "repeat_against": "",
        "noRetry": no_retry,
        "getOnlyTokens": "undefined",
        "log_id": "",
        "app_name": app_name,
        "_": int(time.time() * 1000),
        "sid": sid,
    }
    if method == "GET":
        r = session.get(api_url, params=params, headers=headers, timeout=timeout)
    else:
        r = session.post(
            api_url,
            params=params,
            json={"formValues": form_values},
            headers=headers,
            timeout=timeout,
        )
    r.raise_for_status()
    return r.json()


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Every AchieveForms/Firmstep council performs the same init_session()
# handshake before any data can be fetched, then POSTs one or more
# apibroker/runLookup calls with a {section: {field: {"value": ...}}} payload.
# Where councils genuinely differ:
#
#   * how many runLookup calls are needed (one; or a "get a token" call
#     followed by the real data call, the token/session threaded from the
#     first response into the second's formValues);
#   * the shape of the *final* call's rows_data (one row per collection; a
#     single wide "row 0" with a separate date field per waste type; a JSON
#     string embedded inside a field of row 0).
#
# AchieveFormsRetriever covers the handshake-plus-N-lookups acquisition (HTTP
# only, still returns the raw response); LookupStep declares one call in that
# chain. AchieveFormsRowsParser does the one universal bit of interpretation
# (unwrap integration.transformed.rows_data) with no I/O. The two shape
# preprocessors below (wide single-row field map; JSON-embedded-in-a-field)
# cover two of the response shapes found across the ~20 dependent sources;
# a genuinely different shape (a dynamic-key row, or an HTML fragment inside a
# field) still fits the pipeline but needs a source- or preprocessor-specific
# step of its own, same as FirmstepSelfService's per-source row classifiers.
# --------------------------------------------------------------------------- #


class LookupStep:
    """One ``apibroker/runLookup`` call in an :class:`AchieveFormsRetriever` chain.

    Args:
        lookup_id: the runLookup ``id`` query parameter for this call.
        form_values: ``(context, source) -> dict``, building the fields nested
            under ``section`` (e.g. ``{"UPRN": {"value": ...}}``). ``context``
            is a plain dict shared across every step of the chain: it starts
            empty and carries whatever an earlier step's ``extract`` stored
            (e.g. a token this step's ``form_values`` must include). Optional
            when ``method="GET"`` (a GET call sends no body); defaults to an
            empty dict.
        section: the outer form key this call's fields nest under. AchieveForms
            panels vary here ("Section 1", "Property details", "Address", ...).
        extract: optional ``(response, context) -> None``. Mutates ``context``
            in place with a value read out of this step's raw JSON response
            (typically via ``response["integration"]["transformed"]["rows_data"]``)
            for a later step's ``form_values`` to consume. Omit for the last
            (or only) step, whose response is returned as-is.
        timeout: per-call timeout in seconds.
        method: ``"POST"`` (default), the normal runLookup call, or ``"GET"``
            for a council that fetches a token via a bare GET to the same
            runLookup endpoint (same ``id``/query-params, no JSON body) rather
            than a POST -- e.g. a one-time token issued ahead of the real
            lookup. See :func:`run_lookup`.
        no_retry: value for the ``noRetry`` query-string parameter (default
            ``"false"``; some councils' token calls require ``"true"``).
        headers: optional ``(context, source) -> dict`` of extra request
            headers for this call (e.g. a CSRF token read out of an earlier
            step's response via ``extract`` and required as a header, not a
            form field, on a later step).
        label: optional waste-type label for this step, used only when the
            retriever accumulates every step's response
            (``AchieveFormsRetriever(collect_all=True)``) -- see
            :class:`AchieveFormsMultiLookupRowsParser`. Unused otherwise.
        date_field: optional row field name holding this step's date, also
            only consumed by :class:`AchieveFormsMultiLookupRowsParser`.
    """

    def __init__(
        self,
        lookup_id: str,
        form_values: "Callable[[dict[str, Any], BaseSource], dict] | None" = None,
        *,
        section: str = "Section 1",
        extract: "Callable[[dict, dict[str, Any]], None] | None" = None,
        timeout: int = 30,
        method: str = "POST",
        no_retry: str = "false",
        headers: "Callable[[dict[str, Any], BaseSource], dict[str, str]] | None" = None,
        label: "str | None" = None,
        date_field: "str | None" = None,
    ):
        self.lookup_id = lookup_id
        self.form_values = form_values
        self.section = section
        self.extract = extract
        self.timeout = timeout
        self.method = method
        self.no_retry = no_retry
        self.headers = headers
        self.label = label
        self.date_field = date_field


class GetStep:
    """A bare, authenticated GET call in an :class:`AchieveFormsRetriever` chain.

    For a council whose flow needs a plain GET to an endpoint that isn't a
    ``apibroker/runLookup`` call -- e.g. a CSRF/nonce token fetched from a
    council-specific endpoint before the main lookup. Unlike :class:`LookupStep`,
    no ``id``/``formValues`` plumbing is applied: the URL is used as given, with
    ``sid`` always added to the query params.

    Args:
        url: the URL to GET. A literal string, or a ``(context, source) ->
            str`` callable for a URL built from an earlier step's context or
            source.params.
        extract: ``(response, context) -> None``. Mutates ``context`` in
            place with a value read out of this call's raw JSON response, for
            a later step's ``form_values``/``headers``/``params`` to consume.
            A ``GetStep`` with no ``extract`` has no observable effect on the
            chain, so one is required.
        params: optional ``(context, source) -> dict`` for extra query params
            beyond ``sid``.
        headers: optional ``(context, source) -> dict`` of extra request
            headers for this call.
        timeout: per-call timeout in seconds.
    """

    def __init__(
        self,
        url: "str | Callable[[dict[str, Any], BaseSource], str]",
        *,
        extract: "Callable[[dict, dict[str, Any]], None]",
        params: "Callable[[dict[str, Any], BaseSource], dict] | None" = None,
        headers: "Callable[[dict[str, Any], BaseSource], dict[str, str]] | None" = None,
        timeout: int = 30,
    ):
        self.url = url
        self.extract = extract
        self.params = params
        self.headers = headers
        self.timeout = timeout


class AchieveFormsRetriever(RetrieverFunc):
    """Perform the AchieveForms handshake, then one or more runLookup calls.

    Wire a source with::

        retrieve = AchieveFormsRetriever(
            hostname="tendring-self.achieveservice.com",
            service_page="Rubbish_and_recycling_collection_days",
            steps=[
                LookupStep(
                    "6347acbadc425",
                    section="Address",
                    form_values=lambda ctx, source: {
                        "selectedUPRN": {"value": source.params["uprn"]}
                    },
                ),
            ],
        )

    A two-call ("get a token, then fetch") council adds a second step and an
    ``extract`` on the first::

        def _extract_token(response, context):
            context["token"] = response["integration"]["transformed"]["rows_data"]["0"]["token"]

        steps = [
            LookupStep("<token-lookup-id>", form_values=lambda ctx, source: {...}, extract=_extract_token),
            LookupStep("<data-lookup-id>", form_values=lambda ctx, source: {
                "token": {"value": ctx["token"]},
                "uprn": {"value": source.params["uprn"]},
            }),
        ]

    Args:
        hostname: the AchieveForms hostname (e.g.
            ``"tendring-self.achieveservice.com"``). Used for the session
            handshake and, unless overridden below, to derive the standard
            endpoint URLs.
        steps: one :class:`LookupStep` (or :class:`GetStep`, for a plain GET
            mid-chain) per call, run in order. The last step's raw JSON
            response is returned unparsed, unless ``collect_all`` is set.
        service_page: shorthand for the common landing-page path,
            ``https://{hostname}/en/service/{service_page}``. Ignored when
            ``initial_url`` is given directly.
        initial_url: the service landing page GET, when the council's path
            doesn't fit the ``service_page`` shorthand (e.g. an
            ``/en/AchieveForms/?form_uri=...`` landing URL). One of
            ``initial_url`` / ``service_page`` is required.
        auth_url / api_url: override the derived
            ``https://{hostname}/authapi/isauthenticated`` /
            ``https://{hostname}/apibroker/runLookup`` endpoints, for a council
            that proxies them under a different host/path.
        auth_test_url: optional ``apibroker/domain/<hostname>`` warm-up GET,
            passed straight through to :func:`init_session`.
        skip_landing_page: when True, don't GET ``initial_url`` — use it
            verbatim as the auth call's ``uri`` value. For a council whose
            landing page itself 403s a non-browser GET (a bot-check in front
            of the page, but not in front of ``authapi``); see
            :func:`init_session`.
        timeout: handshake timeout in seconds. Each step has its own timeout
            for its runLookup call.
        collect_all: when True, return a ``list`` of every step's raw response
            (in step order) instead of just the last one. For a council that
            needs one independent runLookup per bin type rather than a
            token-passing chain -- pair with
            :class:`AchieveFormsMultiLookupRowsParser`, which reads each
            step's ``label``/``date_field`` back off ``source.retrieve.steps``
            to know which response is which.
    """

    def __init__(
        self,
        *,
        hostname: str,
        steps: "list[LookupStep | GetStep]",
        service_page: "str | None" = None,
        initial_url: "str | None" = None,
        auth_url: "str | None" = None,
        api_url: "str | None" = None,
        auth_test_url: "str | None" = None,
        skip_landing_page: bool = False,
        timeout: int = 30,
        collect_all: bool = False,
    ):
        if not initial_url and not service_page:
            raise ValueError(
                "AchieveFormsRetriever requires either initial_url or service_page"
            )
        self.hostname = hostname
        self.steps = steps
        self.service_page = service_page
        self._initial_url = initial_url
        self._auth_url = auth_url
        self._api_url = api_url
        self.auth_test_url = auth_test_url
        self.skip_landing_page = skip_landing_page
        self.timeout = timeout
        self.collect_all = collect_all

    @property
    def initial_url(self) -> str:
        return (
            self._initial_url
            or f"https://{self.hostname}/en/service/{self.service_page}"
        )

    @property
    def auth_url(self) -> str:
        return self._auth_url or f"https://{self.hostname}/authapi/isauthenticated"

    @property
    def api_url(self) -> str:
        return self._api_url or f"https://{self.hostname}/apibroker/runLookup"

    def __call__(self, source: "BaseSource") -> "dict | list[dict]":
        session = source.session
        sid = init_session(
            session,
            self.initial_url,
            self.auth_url,
            self.hostname,
            auth_test_url=self.auth_test_url,
            timeout=self.timeout,
            skip_landing_page=self.skip_landing_page,
        )
        context: dict[str, Any] = {}
        result: dict = {}
        results: list[dict] = []
        for step in self.steps:
            if isinstance(step, GetStep):
                url = step.url(context, source) if callable(step.url) else step.url
                params: dict[str, Any] = {"sid": sid}
                if step.params is not None:
                    params.update(step.params(context, source))
                headers = step.headers(context, source) if step.headers else None
                r = session.get(
                    url, params=params, headers=headers, timeout=step.timeout
                )
                r.raise_for_status()
                result = r.json()
                step.extract(result, context)
            else:
                form_values = (
                    step.form_values(context, source) if step.form_values else {}
                )
                headers = step.headers(context, source) if step.headers else None
                result = run_lookup(
                    session,
                    self.api_url,
                    sid,
                    step.lookup_id,
                    {step.section: form_values},
                    timeout=step.timeout,
                    no_retry=step.no_retry,
                    method=step.method,
                    headers=headers,
                )
                if step.extract is not None:
                    step.extract(result, context)
            results.append(result)
        return results if self.collect_all else result


class AchieveFormsRowsParser(Parser[Any]):
    """Unwrap ``integration.transformed.rows_data`` from an AchieveForms response.

    Does no further interpretation: ``rows_data`` comes back from the platform
    as either a dict keyed by row index (``{"0": {...}, "1": {...}}``) or,
    less often, a bare list — this returns it unchanged so a preprocessor can
    handle whichever shape this council's lookup returns. No I/O, so it runs
    standalone against a cached JSON fixture.
    """

    def __call__(self, raw: dict, source: "BaseSource | None" = None) -> Any:
        rows = raw.get("integration", {}).get("transformed", {}).get("rows_data")
        response_shape.expect(
            isinstance(rows, (dict, list)),
            source_name=response_shape.source_name(source),
            detail="AchieveForms response missing integration.transformed.rows_data",
            raw=raw,
        )
        return rows


class LabelField(str):
    """Marker: use another row field as the label, not a fixed string.

    In an :class:`AchieveFormsFieldMapPreprocessor` ``fields`` entry, wrap the
    label in ``LabelField(...)`` when the human-readable waste-type name is
    itself a field on the row (e.g. a service's display name alongside its
    next-collection date), rather than a name the source would otherwise
    hard-code::

        fields=[
            ("FoodWasteServiceNextCollection", LabelField("FoodWasteServiceName")),
            ("GardenWasteServiceNextCollection", LabelField("GardenWasteServiceName")),
        ]

    A plain ``str`` label (not wrapped) is used as-is, unchanged from before.
    Subclassing ``str`` keeps :data:`FieldMapEntry`'s element type a plain
    ``str`` while remaining distinguishable via ``isinstance(label, LabelField)``.
    """

    __slots__ = ()


# A field-map entry is either (date_field, label) or, when the waste type is
# only collected for some properties, (date_field, label, condition_field).
# ``label`` is either a literal string or a :class:`LabelField` (read the
# label from another field on the same row).
FieldMapEntry: TypeAlias = "tuple[str, str] | tuple[str, str, str]"


def _looks_true(value: Any) -> bool:
    """AchieveForms represents booleans as strings; treat the common truthy ones."""
    return str(value).strip().lower() in {"true", "yes", "1"}


class AchieveFormsFieldMapPreprocessor(
    preprocessors.Preprocessor[Any, "tuple[Any, str]"]
):
    """Turn one wide AchieveForms row into ``(date, label)`` records.

    Several AchieveForms lookups return a *single* summary row with a separate
    date field per waste type (and sometimes an eligibility field) rather than
    one row per collection::

        preprocess = AchieveFormsFieldMapPreprocessor(
            fields=[
                ("nextResidualCollection", "Residual waste"),
                ("nextGreenCollection", "Green recycling box"),
                ("nextFoodCollection", "Food waste", "eligibleFoodCollection"),
            ],
        )
        transform = RowTransformer(type_value_map={...})

    Args:
        fields: a list of ``(date_field, label)`` or ``(date_field, label,
            condition_field)`` entries (see :data:`FieldMapEntry`). ``label``
            is a literal string by default; wrap it in ``LabelField(...)`` to
            read the label from another field on the same row instead (a
            service's own display name) -- see :class:`LabelField`. When a
            ``condition_field`` is given, that waste type is skipped unless the
            row's value for it looks true (AchieveForms represents booleans as
            the strings ``"True"``/``"False"``).
        row_key: the key of the row to read when the parsed value is a dict
            keyed by row index (default ``"0"``, the common single-row shape).
            Ignored when the parsed value is already a single flat dict.
        min_year: a parsed date whose year is under this is treated as
            AchieveForms' "no next collection scheduled" sentinel (e.g.
            ``0001-01-01``) and skipped. Default 2000.
        parse_date: a ``date_parsers`` callable used to parse each field's raw
            string (and to evaluate ``min_year``). Defaults to
            ``date_parsers.auto``; pass an explicit
            ``date_parsers.for_format(...)`` for a day-first (or otherwise
            ambiguous) format such as UK ``DD/MM/YYYY``, since dateutil's auto
            mode is month-first by default.
        truncate: when set, each field's raw string is sliced to this many
            leading characters before parsing (e.g. ``truncate=10`` to drop a
            trailing ``" HH:MM:SS"`` AchieveForms sometimes appends to a
            otherwise-fixed-width date).
    """

    def __init__(
        self,
        fields: "list[FieldMapEntry]",
        *,
        row_key: str = "0",
        min_year: int = 2000,
        parse_date: "Any | None" = None,
        truncate: "int | None" = None,
    ):
        from waste_collection_schedule import date_parsers

        self.fields = fields
        self.row_key = row_key
        self.min_year = min_year
        self.parse_date = parse_date or date_parsers.auto
        self.truncate = truncate

    def __call__(self, rows: Any, source: "BaseSource | None" = None) -> "Any":
        if isinstance(rows, dict) and self.row_key in rows:
            row = rows[self.row_key]
        elif isinstance(rows, dict):
            row = rows
        elif rows:
            row = rows[0]
        else:
            row = {}
        if not isinstance(row, dict):
            return

        for entry in self.fields:
            date_field, label = entry[0], entry[1]
            condition_field = entry[2] if len(entry) > 2 else None
            if condition_field and not _looks_true(row.get(condition_field)):
                continue
            if isinstance(label, LabelField):
                resolved_label = str(row.get(str(label)) or "").strip()
                if not resolved_label:
                    continue
            else:
                resolved_label = label
            raw_date = str(row.get(date_field) or "").strip()
            if not raw_date:
                continue
            if self.truncate is not None:
                raw_date = raw_date[: self.truncate]
            try:
                parsed = self.parse_date(raw_date)
            except (ValueError, TypeError):
                continue
            if parsed.year < self.min_year:
                continue
            yield parsed, resolved_label


class AchieveFormsJsonRowsPreprocessor(preprocessors.Preprocessor[Any, dict]):
    """Decode a JSON-string field embedded in a summary row into row dicts.

    Some AchieveForms lookups return the real per-collection records as a
    JSON-encoded string nested inside a field of the single summary row
    (e.g. a Bartec-backed council's ``jobsJSON`` field) rather than as
    ``rows_data`` entries directly::

        preprocess = AchieveFormsJsonRowsPreprocessor(json_field="jobsJSON")
        transform = JsonTransformer(
            date_key="jobDate",
            type_key=lambda r: r.get("jobType") or r.get("jobName") or "Unknown",
            type_value_map={...},
        )

    Args:
        json_field: the row field name holding the JSON-encoded list string.
        row_key: the key of the summary row to read (default ``"0"``).
        dedupe_key: optional ``(item) -> Hashable``; when given, a later item
            producing the same key as an earlier one is dropped (the
            provider's job feed can repeat an entry).
    """

    def __init__(
        self,
        json_field: str,
        *,
        row_key: str = "0",
        dedupe_key: "Callable[[dict], Hashable] | None" = None,
    ):
        self.json_field = json_field
        self.row_key = row_key
        self.dedupe_key = dedupe_key

    def __call__(self, rows: Any, source: "BaseSource | None" = None) -> "Any":
        row = rows.get(self.row_key, {}) if isinstance(rows, dict) else {}
        raw = row.get(self.json_field) if isinstance(row, dict) else None
        try:
            items = json.loads(raw) if raw else []
        except (ValueError, TypeError):
            response_shape.expect(
                False,
                source_name=response_shape.source_name(source),
                detail=f"{self.json_field!r} field is not valid JSON",
                raw=raw,
            )
            return

        seen: set[Hashable] = set()
        for item in items:
            if self.dedupe_key is not None:
                key = self.dedupe_key(item)
                if key in seen:
                    continue
                seen.add(key)
            yield item


class AchieveFormsDynamicRowsPreprocessor(
    preprocessors.Preprocessor[Any, "tuple[Any, str]"]
):
    """Turn one wide AchieveForms row into ``(date, label)`` records, where the
    waste-type labels come from the row's OWN key names rather than a fixed
    ``fields=`` list.

    Some AchieveForms lookups return a summary row whose bin-type fields
    aren't a small fixed set: the field name itself carries the label, and a
    property may even carry two competing variants of the same field (e.g.
    Highland's ``refuseNextDateOld`` / ``refuseNextDateNew``, switched per
    property by another flag on the row). ``key_pattern`` is matched against
    every key in the row; its single capture group becomes the label::

        preprocess = AchieveFormsDynamicRowsPreprocessor(
            re.compile(r"^(.+?)NextDate(?:New|Old)?$"),
        )
        transform = RowTransformer(type_value_map={...})

    Args:
        key_pattern: a compiled regex (or pattern string) matched against
            each row key, with exactly one capture group -- the label. Keys
            that don't match, or whose value is falsy, are skipped.
        row_key: the key of the row to read when the parsed value is a dict
            keyed by row index (default ``"0"``). Ignored when the parsed
            value is already a single flat dict.
        split_label: split a PascalCase captured label into words
            (``"GeneralWaste"`` -> ``"General Waste"``). Default False (most
            AchieveForms key prefixes are already a single lower-case word;
            set True for a provider whose keys are genuinely PascalCase).
        key_filter: optional ``(key, row) -> bool`` called for every
            pattern-matching key, to resolve a per-row ambiguity such as
            Highland's New/Old variant switch -- return False to skip that
            key for this row. Default: every matching key is used.
        min_year: a parsed date whose year is under this is treated as
            AchieveForms' "no next collection scheduled" sentinel and
            skipped. Default 2000.
        parse_date: a ``date_parsers`` callable used to parse each matched
            value. Defaults to ``date_parsers.auto``.
    """

    def __init__(
        self,
        key_pattern: "str | re.Pattern[str]",
        *,
        row_key: str = "0",
        split_label: bool = False,
        key_filter: "Callable[[str, dict], bool] | None" = None,
        min_year: int = 2000,
        parse_date: "Any | None" = None,
    ):
        from waste_collection_schedule import date_parsers

        self.key_pattern = (
            re.compile(key_pattern) if isinstance(key_pattern, str) else key_pattern
        )
        self.row_key = row_key
        self.split_label = split_label
        self.key_filter = key_filter
        self.min_year = min_year
        self.parse_date = parse_date or date_parsers.auto

    def __call__(self, rows: Any, source: "BaseSource | None" = None) -> "Any":
        if isinstance(rows, dict) and self.row_key in rows:
            row = rows[self.row_key]
        elif isinstance(rows, dict):
            row = rows
        elif rows:
            row = rows[0]
        else:
            row = {}
        if not isinstance(row, dict):
            return

        for key, value in row.items():
            if not value:
                continue
            match = self.key_pattern.match(key)
            if not match:
                continue
            if self.key_filter is not None and not self.key_filter(key, row):
                continue
            label = match.group(1)
            if self.split_label:
                label = re.sub(r"(?<!^)(?=[A-Z])", " ", label).strip()
            try:
                parsed = self.parse_date(str(value))
            except (ValueError, TypeError):
                continue
            if parsed.year < self.min_year:
                continue
            yield parsed, label


class AchieveFormsMultiLookupRowsParser(Parser[Any]):
    """Unwrap rows from EVERY response of a ``collect_all=True`` retriever.

    Some councils need one independent runLookup call per bin type (no shared
    token/context between them) rather than a single call or a token-passing
    chain -- wire the retriever with ``AchieveFormsRetriever(collect_all=True,
    steps=[LookupStep(..., label=..., date_field=...), ...])`` so ``retrieve``
    returns the list of raw responses, one per step, in step order. This
    parser zips that list back up with ``source.retrieve.steps`` (the
    authoritative record of which step produced which response) and yields
    ``(date, label)`` tuples straight from each step's own row/date field, no
    further preprocessing needed::

        retrieve = AchieveFormsRetriever(
            hostname=HOSTNAME,
            collect_all=True,
            steps=[
                LookupStep(id1, form_values=..., label="Household Waste", date_field="DWDate"),
                LookupStep(id2, form_values=..., label="Recycling", date_field="MDRDate"),
            ],
        )
        parse = AchieveFormsMultiLookupRowsParser()
        transform = RowTransformer(parse_date=date_parsers.for_format("%d/%m/%Y"), type_value_map={...})

    A step whose lookup found nothing (e.g. an unsubscribed service) returns
    an empty ``rows_data`` ( ``{}`` or ``[]``); it simply contributes no rows.
    """

    def __call__(self, raw: "list[dict]", source: "BaseSource | None" = None) -> Any:
        steps = getattr(getattr(source, "retrieve", None), "steps", None) or []
        for response, step in zip(raw, steps, strict=False):
            if not isinstance(response, dict):
                continue
            if response.get("result") == "logout":
                response_shape.expect(
                    False,
                    source_name=response_shape.source_name(source),
                    detail="AchieveForms session was rejected (logout)",
                    raw=response,
                )
            rows = (
                response.get("integration", {}).get("transformed", {}).get("rows_data")
            )
            values = (
                rows.values()
                if isinstance(rows, dict)
                else rows
                if isinstance(rows, list)
                else []
            )
            date_field = getattr(step, "date_field", None)
            label = getattr(step, "label", None)
            for row in values:
                if not isinstance(row, dict) or not date_field:
                    continue
                date_str = row.get(date_field)
                if not date_str:
                    continue
                yield date_str, label
