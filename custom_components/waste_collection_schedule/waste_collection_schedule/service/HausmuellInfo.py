"""Shared client for the hausmüll.info ("aturis eko") calendar platform (DE).

A number of German operators publish their collection calendar through the
same backend, reachable either at ``<operator>.hausmuell.info`` or mirrored
onto the operator's own domain. Every deployment works the same way:

* the address is resolved one level at a time (Ort, Ortsteil, Straße,
  Hausnummer, and on some deployments an object number), each level a POST
  whose response is a proposal list::

      <ul><li id='str_82121' onClick='get_value("str",82121,0)'>
            <span style='display:none;'>82121</span>
            <span style='display:none;'>0</span>
            <span>Bördestraße</span></li></ul>

  The onclick carries the level's own id and, once the address is specific
  enough, the disposal area ("Entsorgungsgebiet") id that actually selects the
  schedule. The first proposal is the one taken;
* every resolved id is threaded into the next level's request, so the levels
  cannot be issued in parallel;
* the calendar itself is a final POST to ``ics/ics.php`` carrying the resolved
  ids, which returns ICS for ``parsers.IcsParser``.

Deployments differ only in how the lookup is addressed. Two dialects exist,
and the same host can serve both:

* **proxy dialect** -- every level goes to one ``proxy.php``, and an op-code in
  the body's ``url`` field says which level is being asked for;
* **search dialect** -- one endpoint per level under ``search/``, with the ids
  in the query string and the whole accumulating form in the body.

:class:`HausmuellInfoRetriever` is the whole flow for both, so a source on this
platform declares only its URLs, its form template and its levels.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.retrievers import Response, RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

AREA = "area"
"""Key under which the resolved disposal-area id is offered to ``calendar_data``."""

UNRESOLVED = "0"
"""The id the platform returns for "no such entity at this level (yet)"."""

CHECK_ZUSATZ_PATH = "search/check_zusatz.php"
HNR_ID_KEY = "hidden_id_hnr"
ZUSATZ_ID_KEY = "hidden_id_zusatz"

_REDIRECT_STATUSES = (301, 302, 303, 307, 308)
_MAX_REDIRECTS = 5

# curl_cffi's ``data=`` (unlike plain ``requests``) stringifies a list value
# (``{"input_str": ["a", "a"]}`` becomes the literal text ``"['a', 'a']"``)
# instead of repeating the key, and the search dialect's endpoints only work
# with the latter. Those deployments therefore pre-encode the body with
# ``doseq=True``, which also means the Content-Type curl_cffi would infer for a
# dict body must be set explicitly: a raw string body defaults to
# application/octet-stream and the server won't populate $_POST from it.
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

_UMLAUT_FOLDINGS = {
    "ß": "s",
    "ä": "a",
    "ö": "o",
    "ü": "u",
    "Ä": "A",
    "Ö": "O",
    "Ü": "U",
}


def fold_umlauts(value: str) -> str:
    """Transliterate the German special characters to plain ASCII."""
    for char, replacement in _UMLAUT_FOLDINGS.items():
        value = value.replace(char, replacement)
    return value


def blank_umlauts(value: str) -> str:
    """Replace every German special character with the SQL single-character wildcard."""
    for char in _UMLAUT_FOLDINGS:
        value = value.replace(char, "_")
    return value


def _fold_one(value: Any, fold: Callable[[str], str]) -> Any:
    if isinstance(value, list):
        return [_fold_one(item, fold) for item in value]
    return fold(value) if isinstance(value, str) else value


def _fold_values(data: Mapping[str, Any], fold: Callable[[str], str]) -> dict[str, Any]:
    """Apply ``fold`` to every value, including the members of a list value."""
    return {key: _fold_one(value, fold) for key, value in data.items()}


def parse_proposal_ids(html: str) -> list[str]:
    """The numeric ids the platform hides in the first proposal's onclick.

    ``get_value("hnr",1194011,1205137)`` yields ``["1194011", "1205137"]``: the
    level's own id, then the disposal area. Deployments that do not resolve an
    area at this level emit a single id (and append
    ``event.stopPropagation();``, which carries no digits and drops out).
    """
    li = BeautifulSoup(html, "html.parser").find("li", attrs={"onclick": True})
    if not isinstance(li, Tag):
        return []
    onclick = li.get("onclick")
    if not isinstance(onclick, str):
        return []
    ids = onclick.split(")")[0].split("(")[1].split(",")
    return [i.strip() for i in ids if i.strip().isdigit()]


def has_proposal(html: str) -> bool:
    """Whether a lookup response actually contains a matching entry.

    A real match is a ``<li>`` with an ``onclick``; nothing matching is either
    an empty ``<ul>`` or a ``<li>Keinen Eintrag gefunden</li>`` without one.
    Detecting the onclick is robust to the exact "not found" wording and
    markup, which the literal-string checks got wrong (see #6877).
    """
    return parse_proposal_ids(html) != []


@dataclass(frozen=True)
class FromForm:
    """A query-string value read out of the accumulating form at request time."""

    key: str


@dataclass(frozen=True)
class Lookup:
    """One level of the platform's address cascade.

    Args:
        field: the source param holding the search term, and the argument
            blamed when the level does not resolve.
        endpoint: path under the deployment's base URL (search dialect). Empty
            for the proxy dialect, which sends every level to the retriever's
            single ``lookup_url``.
        opcode: value written into the form's ``url`` field to say which level
            is being asked for (proxy dialect).
        query: query-string keys sent alongside the form (search dialect); a
            :class:`FromForm` value is read out of the accumulating form. The
            search term is always sent first as ``input``, so it is implicit.
            An empty mapping sends no query string at all.
        assign: form keys that receive the resolved id, in order. A key that is
            not already in the form is appended, which is how the platform's
            own page orders its fields.
        zero_falls_back_to: form key whose value is used instead when the level
            resolves to id ``"0"``. An Ortsteil that is not a separate entity
            keeps its Ort's id.
        set_input: write the search term into the form's ``input`` field before
            the request. The field is stale on the levels that leave it alone,
            but it is on the wire, so it is reproduced per level.
        skip_if_blank: skip the level when the term is empty. True for the
            optional levels of an address cascade; False for a level the source
            declares mandatory, which posts an empty term the way the
            platform's own form does.
        only_if_area_unresolved: run only while no disposal area has been
            resolved. Some addresses do not name an area from street and house
            number alone and need an extra identifier before the platform will.
        required_message: reason given to ``SourceArgumentRequired`` when
            ``only_if_area_unresolved`` selects this level and the term is
            empty. ``None`` leaves the level optional.
    """

    field: str
    endpoint: str = ""
    opcode: int | None = None
    query: Mapping[str, Any] = dataclass_field(default_factory=dict)
    assign: tuple[str, ...] = ()
    zero_falls_back_to: str | None = None
    set_input: bool = True
    skip_if_blank: bool = True
    only_if_area_unresolved: bool = False
    required_message: str | None = None


class HausmuellInfoRetriever(RetrieverFunc):
    """Resolve the address cascade, then POST for the ICS calendar.

    The pipeline retrieve step for the platform: it walks ``steps``, threading
    each level's resolved id into the next level's request through one
    accumulating form, and posts the result to the deployment's ``ics/ics.php``.

    Args:
        base_url: the deployment's base URL, ending in ``/``. A callable is
            resolved against ``source.params`` (the subdomain is a user
            argument on the multi-operator source).
        steps: the address cascade, outermost level first.
        form: the initial request body, as a mapping or a callable resolved
            against ``source.params``. Its key order is the wire order, so
            declare it the way the deployment's own form does.
        lookup_url: the single lookup endpoint of the proxy dialect. Ignored by
            a step that carries its own ``endpoint``. It may sit on another host
            entirely: some operators mirror the lookup on their own domain while
            the calendar stays on hausmuell.info.
        calendar_path: path of the calendar request under ``base_url``.
        calendar_data: builds the calendar body, called as
            ``calendar_data(ids, **source.params)`` where ``ids`` maps each
            resolved level's field to its id plus :data:`AREA` to the disposal
            area. ``None`` posts the accumulating form itself, which is what the
            search dialect does.
        area_key: form key mirroring the resolved disposal area. ``None`` keeps
            it out of the form and offers it only through ``ids``.
        landing_page: GET ``base_url`` before the cascade and copy its
            ``showBins*`` checkboxes into the form. Redirects are followed by
            hand (some operators permanently redirect their hausmuell.info
            subdomain to their own domain) so each hop stays a separately
            recorded interaction, and the redirect target becomes the base URL
            for the rest of the flow.
        check_zusatz: ask ``search/check_zusatz.php`` for the address's
            "Zusatz" id before the calendar request. The endpoint is absent on
            deployments without the concept and answers 500, which is why its
            status is not checked; the house-number id stands in.
        repeat_list_values: pre-encode the body so a list value repeats its key
            rather than being stringified (see :data:`FORM_HEADERS`).
        retry_folded: retry a level that matched nothing with its special
            characters transliterated, then with them wildcarded. The search
            endpoints are inconsistent about matching "ß" and umlauts verbatim.
        encoding: response encoding forced on the calendar response before its
            ``.text`` is read. Some deployments mis-declare their charset, and
            some HTTP clients (curl_cffi included) cache the decoded text on
            first read and refuse a later re-decode.
        rejected_text: text the platform's error page carries when it will not
            accept the address at all. Raises against ``rejected_field``.
        rejected_field: the argument blamed for ``rejected_text``.
        check_lookup_status: raise on an error status from a lookup.
        check_calendar_status: raise on an error status from the calendar.
    """

    def __init__(
        self,
        *,
        base_url: str | Callable[..., str],
        steps: Sequence[Lookup],
        form: Mapping[str, Any] | Callable[..., Mapping[str, Any]],
        lookup_url: str = "",
        calendar_path: str = "ics/ics.php",
        calendar_data: Callable[..., Mapping[str, Any]] | None = None,
        area_key: str | None = None,
        landing_page: bool = False,
        check_zusatz: bool = False,
        repeat_list_values: bool = False,
        retry_folded: bool = False,
        encoding: str | None = None,
        rejected_text: str | None = None,
        rejected_field: str = "",
        check_lookup_status: bool = True,
        check_calendar_status: bool = True,
    ):
        if not steps:
            raise ValueError("HausmuellInfoRetriever requires at least one step")
        for step in steps:
            if not step.endpoint and not lookup_url:
                raise ValueError(
                    f"step {step.field!r} has no endpoint and no lookup_url to fall "
                    "back on"
                )
        if bool(rejected_text) != bool(rejected_field):
            raise ValueError("rejected_text and rejected_field go together")
        self._base_url = base_url
        self._steps = tuple(steps)
        self._form = form
        self._lookup_url = lookup_url
        self._calendar_path = calendar_path
        self._calendar_data = calendar_data
        self._area_key = area_key
        self._landing_page = landing_page
        self._check_zusatz = check_zusatz
        self._repeat_list_values = repeat_list_values
        self._retry_folded = retry_folded
        self._encoding = encoding
        self._rejected_text = rejected_text
        self._rejected_field = rejected_field
        self._check_lookup_status = check_lookup_status
        self._check_calendar_status = check_calendar_status

    # --- HTTP ---

    def _post(
        self,
        session: Any,
        url: str,
        data: Mapping[str, Any],
        params: Mapping[str, Any] | None,
    ) -> Response:
        if self._repeat_list_values:
            return session.post(
                url,
                data=urlencode(data, doseq=True),
                params=params,
                headers=FORM_HEADERS,
            )
        if params is None:
            return session.post(url, data=data)
        return session.post(url, data=data, params=params)

    def _open_landing_page(self, session: Any, base_url: str) -> tuple[str, Response]:
        response = session.get(base_url, allow_redirects=False)
        for _ in range(_MAX_REDIRECTS):
            if response.status_code not in _REDIRECT_STATUSES:
                break
            location = response.headers.get("location")
            if not location:
                break
            base_url = urljoin(base_url, location)
            response = session.get(base_url, allow_redirects=False)
        return base_url, response

    # --- cascade ---

    def _lookup(
        self,
        session: Any,
        step: Lookup,
        url: str,
        term: str,
        form: dict[str, Any],
        params: dict[str, Any] | None,
    ) -> list[str]:
        """Ask one level, retrying folded variants where the deployment needs it."""
        attempts: list[tuple[Mapping[str, Any], Mapping[str, Any] | None]] = [
            (form, params)
        ]
        if self._retry_folded:
            folded_params = (
                None if params is None else _fold_values(params, fold_umlauts)
            )
            attempts.append((_fold_values(form, fold_umlauts), folded_params))
            attempts.append((_fold_values(form, blank_umlauts), folded_params))

        for data, query in attempts:
            response = self._post(session, url, data, query)
            if self._check_lookup_status:
                response.raise_for_status()
            ids = parse_proposal_ids(response.text)
            if ids:
                return ids
        raise SourceArgumentNotFoundWithSuggestions(step.field, term, [])

    def _query(self, step: Lookup, term: str, form: dict[str, Any]) -> dict | None:
        if not step.query:
            return None
        query: dict[str, Any] = {"input": term}
        for key, value in step.query.items():
            query[key] = form[value.key] if isinstance(value, FromForm) else value
        return query

    def __call__(self, source: BaseSource) -> Response:
        session = source.session
        params = source.params

        base_url = (
            self._base_url(**params) if callable(self._base_url) else self._base_url
        )
        template = self._form(**params) if callable(self._form) else self._form
        form: dict[str, Any] = dict(template)

        if self._landing_page:
            base_url, landing = self._open_landing_page(session, base_url)
            for tag in BeautifulSoup(landing.text, "html.parser").find_all("input"):
                name = str(tag.get("name") or "")
                if name.startswith("showBins"):
                    form[name] = "on"

        ids: dict[str, str] = {AREA: UNRESOLVED}

        for step in self._steps:
            raw = params.get(step.field)
            term = "" if raw is None else str(raw)

            if step.only_if_area_unresolved:
                if ids[AREA] != UNRESOLVED:
                    continue
                if not term and step.required_message:
                    raise SourceArgumentRequired(step.field, step.required_message)
            if not term and step.skip_if_blank:
                continue

            if step.set_input:
                form["input"] = term
            if step.opcode is not None:
                form["url"] = step.opcode

            url = base_url + step.endpoint if step.endpoint else self._lookup_url
            found = self._lookup(
                session, step, url, term, form, self._query(step, term, form)
            )

            value = found[0]
            if value == UNRESOLVED and step.zero_falls_back_to:
                value = form[step.zero_falls_back_to]
            for key in step.assign:
                form[key] = value
            ids[step.field] = value

            if len(found) > 1:
                ids[AREA] = found[1]
                if self._area_key:
                    form[self._area_key] = found[1]

        if self._check_zusatz:
            response = self._post(session, base_url + CHECK_ZUSATZ_PATH, form, None)
            span = BeautifulSoup(response.text, "html.parser").find("span")
            form[ZUSATZ_ID_KEY] = (
                form[HNR_ID_KEY] if span is None else span.text.strip()
            )

        data = self._calendar_data(ids, **params) if self._calendar_data else form
        calendar = self._post(session, base_url + self._calendar_path, data, None)
        if self._check_calendar_status:
            calendar.raise_for_status()
        if self._encoding:
            calendar.encoding = self._encoding
        if self._rejected_text and self._rejected_text in calendar.text:
            raise SourceArgumentNotFoundWithSuggestions(
                self._rejected_field, params.get(self._rejected_field), []
            )
        return calendar
