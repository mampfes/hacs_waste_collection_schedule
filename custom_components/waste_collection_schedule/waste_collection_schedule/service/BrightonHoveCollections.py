"""Brighton & Hove BartecCollective collections (Mendix ``Jobs_Get_Combined``).

The council portal at ``enviroservices.brighton-hove.gov.uk`` is a Mendix
client over Bartec. A lookup is one session:

1. ``GET link/collections`` mints the session cookies.
2. ``POST xas/ get_session_data`` answers the CSRF token, the cache-bust key,
   the address and collection objects, and the form to open.
3. The form page names the ``runtimeOperation`` ids (search, select, next
   collections). They are read off the page: a republish changes the ids and
   leaves the widget ids in place.
4. Search by postcode, select the address whose UPRN matches, then ask for the
   jobs. The reply's ``Collections.CollectionsReturned`` rows are the schedule.

The search call sends the address object only. Sending the collection object
with it makes the runtime answer HTTP 560.

:class:`BrightonHoveRetriever` returns the jobs reply.
:class:`BrightonHoveParser` reads it into ``(date, collection type)`` rows.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import date_parsers, response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    import datetime

    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_SESSION_PARAMS = {
    "hybrid": False,
    "offline": False,
    "referrer": None,
    "profile": "",
    "timezoneoffset": 0,
    "timezoneId": "Europe/London",
    "preferredLanguages": ["en-GB", "en"],
    "version": 2,
}
_POSTCODE = re.compile(r"[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}")
_OPERATION_ID = re.compile(r'"operationId"\s*:\s*"([^"]+)"')
_FIND_WIDGET = (
    "p.BHCCTheme.Template_SearchFieldOnly.actionButton3"
    ".BartecCollective.Jobs_Get_Combined"
)
_SELECT_WIDGET = "p.BartecCollective.Jobs_Get_Combined.referenceSelector1"
_NEXT_WIDGET = "p.BartecCollective.Jobs_Get_Combined.actionButton5"
_ADDRESS_TYPE = "BHCCTheme.Address"
_COLLECTION_TYPE = "Collections.Collection"
_RETURNED_TYPE = "Collections.CollectionsReturned"
_LIST_OF_ADDRESSES = "BHCCTheme.AddressTemp_ListOfAddresses"
_SELECTED_ADDRESS = "BHCCTheme.AddressTemp_SelectedAddress"
_NOT_SUBSCRIBED = "not currently subscribed"
_SUGGESTION_LIMIT = 25

_EPOCH = date_parsers.from_epoch("ms")
_TEXT_DATE = date_parsers.auto


def _format_postcode(value: str) -> str:
    """``bn20gd`` and ``BN2 0GD`` both become ``BN2 0GD``; anything else is kept."""
    compact = re.sub(r"\s+", "", value).upper()
    if _POSTCODE.fullmatch(compact):
        return f"{compact[:-3]} {compact[-3:]}"
    return re.sub(r"\s+", " ", value).strip()


def _uprn_key(value: Any) -> str:
    return str(value).strip().lstrip("0")


def _change_value(change: Mapping[str, Any], name: str) -> Any:
    entry = change.get(name)
    if isinstance(entry, dict) and "value" in entry:
        return entry["value"]
    return None


def _field(attrs: Any, change: Any, name: str) -> Any:
    for bag in (attrs, change):
        if not isinstance(bag, Mapping):
            continue
        entry = bag.get(name)
        if isinstance(entry, dict) and "value" in entry:
            return entry["value"]
        if entry is not None and not isinstance(entry, dict):
            return entry
    return None


def _validation_message(payload: Mapping[str, Any]) -> str | None:
    for block in payload.get("datavalidation") or []:
        if not isinstance(block, dict):
            continue
        for field in block.get("errorFields") or []:
            if isinstance(field, dict) and field.get("message"):
                return str(field["message"])
    return None


def _operation_id(
    page: str, widget_id: str, *, on_change: bool, source_name: str
) -> str:
    """The runtime operation a widget declares.

    The first ``actionButton5`` on the page is a visibility rule, so the search
    starts at the widget's own ``$widgetId``. The address selector's first
    operation is its list datasource; the select action is the ``onChange`` one.
    """
    marker = f'$widgetId":"{widget_id}"'
    start = page.find(marker)
    response_shape.expect(
        start >= 0,
        source_name=source_name,
        detail=f"collections page has no widget {widget_id}",
        raw=page[:400],
    )
    window = page[start : start + 12000]
    if on_change:
        at = window.find("onChange")
        response_shape.expect(
            at >= 0,
            source_name=source_name,
            detail=f"widget {widget_id} has no onChange action",
            raw=window[:400],
        )
        window = window[at : at + 4000]
    match = _OPERATION_ID.search(window)
    response_shape.expect(
        match is not None,
        source_name=source_name,
        detail=f"widget {widget_id} names no operationId",
        raw=window[:400],
    )
    assert match is not None
    return match.group(1)


class _MxState:
    """The objects and changes the Mendix client would still be holding.

    A guid stays in ``new`` from ``newpersistable`` until ``commits``. A request
    sends the tracked changes for the guids it names, and the object JSON only
    for those still new.
    """

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, Any]] = {}
        self.changes: dict[str, dict[str, Any]] = {}
        self.new: set[str] = set()

    def apply(self, payload: Mapping[str, Any]) -> None:
        for obj in payload.get("objects") or []:
            if isinstance(obj, dict) and isinstance(obj.get("guid"), str):
                self.objects[obj["guid"]] = obj
        for guid, attrs in (payload.get("changes") or {}).items():
            if not isinstance(attrs, dict):
                continue
            bucket = self.changes.setdefault(guid, {})
            for attr, change in attrs.items():
                if not isinstance(change, dict):
                    continue
                current = bucket.get(attr)
                if "value" in change:
                    bucket[attr] = dict(change)
                elif "hash" in change and isinstance(current, dict):
                    updated = dict(current)
                    updated["hash"] = change["hash"]
                    bucket[attr] = updated
        for entry in payload.get("newpersistable") or []:
            guid = entry.get("guid") if isinstance(entry, dict) else entry
            if isinstance(guid, str):
                self.new.add(guid)
        for entry in payload.get("commits") or []:
            guid = entry.get("guid") if isinstance(entry, dict) else entry
            if isinstance(guid, str):
                self.new.discard(guid)

    def guid_of_type(self, object_type: str) -> str | None:
        for guid, obj in self.objects.items():
            if obj.get("objectType") == object_type:
                return guid
        return None

    def request(
        self,
        operation_id: str,
        params: dict[str, Any],
        guids: list[str],
        validation_guids: list[str],
    ) -> dict[str, Any]:
        changes: dict[str, Any] = {}
        objects: list[dict[str, Any]] = []
        for guid in guids:
            if guid in self.changes:
                changes[guid] = self.changes[guid]
            if guid in self.new and guid in self.objects:
                objects.append(self.objects[guid])
        return {
            "action": "runtimeOperation",
            "operationId": operation_id,
            "params": params,
            "validationGuids": validation_guids,
            "changes": changes,
            "objects": objects,
        }


class BrightonHoveRetriever(RetrieverFunc):
    """Walk the collections form and return the jobs reply.

    Args:
        base_url: the portal host, with or without a trailing slash.
        link: the deep-link target that opens the collections form.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str = "https://enviroservices.brighton-hove.gov.uk/",
        *,
        link: str = "collections",
        timeout: int = 60,
    ):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.link = link.strip("/")
        self.timeout = timeout

    def _expect(
        self, ok: bool, source: BaseSource, detail: str, raw: Any = None
    ) -> None:
        response_shape.expect(
            ok,
            source_name=response_shape.source_name(source),
            detail=detail,
            raw=raw,
        )

    def _post(
        self,
        source: BaseSource,
        csrf: str,
        body: dict[str, Any],
        state: _MxState,
        *,
        read: bool,
    ) -> Response:
        response = source.session.post(
            self.base_url + "xas/",
            json=body,
            headers={"X-Csrf-Token": csrf},
            timeout=self.timeout,
        )
        response.raise_for_status()
        if read:
            state.apply(response.json())
        return response

    def __call__(self, source: BaseSource) -> Response:
        name = response_shape.source_name(source)
        postcode = _format_postcode(str(source.params["postcode"]))
        wanted = _uprn_key(source.params["uprn"])
        session = source.session
        state = _MxState()

        session.get(
            f"{self.base_url}link/{self.link}", timeout=self.timeout
        ).raise_for_status()
        opened = session.post(
            self.base_url + "xas/",
            json={"action": "get_session_data", "params": _SESSION_PARAMS},
            timeout=self.timeout,
        )
        opened.raise_for_status()
        session_data = opened.json()
        state.apply(session_data)

        csrf = session_data.get("csrftoken")
        self._expect(
            isinstance(csrf, str) and bool(csrf),
            source,
            "session response has no CSRF token",
        )
        cachebust = session_data.get("cachebust")
        self._expect(
            cachebust not in (None, ""), source, "session response has no cachebust"
        )

        form_path = None
        for instruction in session_data.get("instructions") or []:
            if isinstance(instruction, dict) and instruction.get("type") == "open_form":
                form_path = (instruction.get("args") or {}).get("FormPath")
                break
        self._expect(
            isinstance(form_path, str) and bool(form_path),
            source,
            "session response does not open a form",
            raw=session_data.get("instructions"),
        )
        locale = session_data.get("locale") or {}
        locale_code = locale.get("code") if isinstance(locale, dict) else None
        locale_code = locale_code or "en_GB"

        page = session.get(
            f"{self.base_url}pages/{locale_code}/{form_path}?{cachebust}",
            timeout=self.timeout,
        )
        page.raise_for_status()
        find_id = _operation_id(
            page.text, _FIND_WIDGET, on_change=False, source_name=name
        )
        select_id = _operation_id(
            page.text, _SELECT_WIDGET, on_change=True, source_name=name
        )
        next_id = _operation_id(
            page.text, _NEXT_WIDGET, on_change=False, source_name=name
        )

        address_guid = state.guid_of_type(_ADDRESS_TYPE)
        collection_guid = state.guid_of_type(_COLLECTION_TYPE)
        self._expect(
            address_guid is not None and collection_guid is not None,
            source,
            "session response has no address and collection objects",
        )
        assert address_guid is not None
        assert collection_guid is not None

        state.changes.setdefault(address_guid, {})["SearchString"] = {"value": postcode}
        found = self._post(
            source,
            csrf,
            state.request(
                find_id,
                {"Address": {"guid": address_guid}},
                [address_guid],
                [address_guid],
            ),
            state,
            read=True,
        )
        # read=True already consumed the body into state; ask for it again.
        # curl_cffi caches the content, and the matcher below needs this reply
        # rather than every change the session has accumulated.
        found_payload = found.json()
        matches = _address_matches(found_payload, address_guid)
        chosen = next((row for row in matches if _uprn_key(row[2]) == wanted), None)
        if chosen is None:
            if not matches:
                message = (
                    _validation_message(found_payload)
                    or "the council did not return any addresses for it."
                )
                raise SourceArgumentNotFound(
                    "postcode", source.params["postcode"], message
                )
            shown = matches[:_SUGGESTION_LIMIT]
            listing = ", ".join(f"{display} ({uprn})" for _guid, display, uprn in shown)
            extra = ""
            if len(matches) > _SUGGESTION_LIMIT:
                extra = f", and {len(matches) - _SUGGESTION_LIMIT} more"
            raise SourceArgumentNotFound(
                "uprn",
                source.params["uprn"],
                f"known properties for this postcode are: {listing}{extra}.",
            )

        state.changes.setdefault(address_guid, {})[_SELECTED_ADDRESS] = {
            "value": chosen[0]
        }
        self._post(
            source,
            csrf,
            state.request(
                select_id,
                {
                    "Collection": {"guid": collection_guid},
                    "Address": {"guid": address_guid},
                },
                [collection_guid, address_guid, chosen[0]],
                [address_guid],
            ),
            state,
            read=True,
        )
        return self._post(
            source,
            csrf,
            state.request(
                next_id,
                {"Collection": {"guid": collection_guid}},
                [collection_guid, address_guid],
                [collection_guid],
            ),
            state,
            read=False,
        )


def _address_matches(
    payload: Mapping[str, Any], address_guid: str
) -> list[tuple[str, str, str]]:
    """``(temp guid, display, uprn)`` rows linked to this search's address."""
    found: list[tuple[str, str, str]] = []
    for guid, change in (payload.get("changes") or {}).items():
        if not isinstance(change, dict):
            continue
        uprn = _change_value(change, "uprn")
        display = _change_value(change, "display")
        owner = _change_value(change, _LIST_OF_ADDRESSES)
        if not uprn or not display or owner != address_guid:
            continue
        found.append((guid, str(display).strip(), str(uprn).strip()))
    found.sort(key=lambda row: (row[1], row[0]))
    return found


def _collection_date(stamp: Any, formatted: Any) -> datetime.date | None:
    if isinstance(stamp, (int, float)) and not isinstance(stamp, bool) and stamp:
        try:
            return _EPOCH(stamp)
        except (TypeError, ValueError, OverflowError, OSError):
            pass
    elif isinstance(stamp, str) and stamp.strip():
        try:
            return _EPOCH(stamp)
        except (TypeError, ValueError, OverflowError, OSError):
            pass
    if isinstance(formatted, str) and formatted.strip():
        try:
            return _TEXT_DATE(formatted)
        except (TypeError, ValueError):
            return None
    return None


def _communal(payload: Mapping[str, Any]) -> bool:
    changes = payload.get("changes") or {}
    for obj in payload.get("objects") or []:
        if not isinstance(obj, dict) or obj.get("objectType") != _COLLECTION_TYPE:
            continue
        attrs = obj.get("attributes") if isinstance(obj.get("attributes"), dict) else {}
        guid = obj.get("guid")
        change = changes.get(guid) if isinstance(guid, str) else {}
        if not isinstance(change, dict):
            change = {}
        if _field(attrs, change, "DisplayCommunal") is True:
            return True
    return False


class BrightonHoveParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, collection type)`` rows from ``Collections.CollectionsReturned``.

    Past jobs and garden-waste placeholders for an unsubscribed property are
    left out. The date is ``collectionDateParse`` (epoch milliseconds, UTC);
    ``Formatted_collection`` is only a fallback.
    """

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        name = response_shape.source_name(source)
        payload = response.json()
        objects = payload.get("objects") if isinstance(payload, dict) else None
        response_shape.expect(
            isinstance(objects, list),
            source_name=name,
            detail="jobs response has no objects list",
            raw=payload if isinstance(payload, dict) else response.text[:400],
        )
        assert isinstance(objects, list)
        changes = payload.get("changes") or {}
        rows: list[tuple[datetime.date, str]] = []
        for obj in objects:
            if not isinstance(obj, dict) or obj.get("objectType") != _RETURNED_TYPE:
                continue
            attrs = (
                obj.get("attributes") if isinstance(obj.get("attributes"), dict) else {}
            )
            guid = obj.get("guid")
            change = changes.get(guid) if isinstance(guid, str) else {}
            if not isinstance(change, dict):
                change = {}
            if _field(attrs, change, "IsPast") is True:
                continue
            status = _field(attrs, change, "BartecStatus")
            if not isinstance(status, str) or not status:
                status = _field(attrs, change, "BartecStatusCopy")
            if isinstance(status, str) and _NOT_SUBSCRIBED in status.casefold():
                continue
            job = _field(attrs, change, "BartecJobID")
            if job in (None, "", 0, False):
                continue
            kind = _field(attrs, change, "Collection_type")
            if not isinstance(kind, str) or not kind.strip():
                continue
            when = _collection_date(
                _field(attrs, change, "collectionDateParse"),
                _field(attrs, change, "Formatted_collection"),
            )
            response_shape.expect(
                when is not None,
                source_name=name,
                detail=f"unparsable collection date for {kind.strip()}",
                raw=obj,
            )
            assert when is not None
            rows.append((when, kind.strip()))
        if not rows and _communal(payload):
            uprn = source.params.get("uprn") if source is not None else None
            raise SourceArgumentNotFound(
                "uprn",
                uprn,
                "this property uses communal bins, which are not published as dated collections.",
            )
        return rows
