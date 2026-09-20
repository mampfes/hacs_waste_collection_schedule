"""Client for the kiedysmieci.info schedule proxy.

kiedysmieci.info fronts the provider's backend through ``schedule-proxy.php``:
one endpoint answering two query types. ``locations`` walks the
voivodeship -> district -> municipality -> street cascade one level at a time,
and ``terms`` returns the schedule for a fully qualified address. Both wrap
their payload in an ``{"ok": ..., "data": ...}`` envelope and report failures
inside it rather than by status alone.

The cascade is what the config flow offers level by level, and it doubles as
the diagnosis for a failed fetch: walking it pinpoints which of the four
arguments is the wrong one.
"""

from typing import Any

import requests

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://kiedysmieci.info/schedule-proxy.php"

TIMEOUT = 30

# The location cascade, from the widest level to the narrowest:
# source argument -> query parameter (which doubles as the key of a returned
# item) -> key holding that level's options in the response.
LOCATION_LEVELS = (
    ("voivodeship", "wojewodztwo", "listaWojewodztw"),
    ("district", "powiat", "listaPowiatow"),
    ("municipality", "gmina", "listaGmin"),
    ("street", "ulica", "listaUlic"),
)

# A known address without a published schedule yields a single placeholder
# entry instead of an empty list.
NO_SCHEDULE_MARKER = "brak harmonogramu"


class KiedySmieciError(Exception):
    """The proxy answered with a failed envelope (``ok`` is not true).

    Distinct from a transport error, which the HTTP client raises, and from a
    wrong address, which this API does not report as a failure at all (see
    ``Source.RAISE_ON_EMPTY``).
    """


def request(
    request_type: str, params: dict[str, Any], session: Any = None
) -> dict[str, Any]:
    """GET one query type and unwrap the response envelope.

    ``session`` is the source's shared client (``source.session``), so the
    retrieve step and the cascade walk that diagnoses its failure go over one
    connection. It is optional because the config flow reaches ``choices()``
    through the ``cascading_select`` classmethod contract, which has no source
    instance to take a session from.
    """
    client = session if session is not None else requests
    response = client.get(
        API_URL, params={"type": request_type} | params, timeout=TIMEOUT
    )

    # Errors are reported in the JSON envelope (with a 4xx/5xx status), so
    # parse the body before looking at the status code.
    try:
        payload = response.json()
    except ValueError:
        response.raise_for_status()
        raise

    if not payload.get("ok"):
        # Two independent pieces of information, and neither is reliably there:
        # the envelope carries the provider's own explanation, the status says
        # whether it failed or refused. A failed envelope can arrive with 200,
        # and a 5xx can arrive carrying no message at all - which used to leave
        # the error as a bare "unexpected response" naming neither.
        message = payload.get("message") or ""
        status = response.status_code
        if status >= 400:
            message = f"{message} (HTTP {status})" if message else f"HTTP {status}"
        raise KiedySmieciError(message or "Unexpected response from kiedysmieci.info")

    return payload.get("data") or {}


def location_params(params: dict[str, Any]) -> dict[str, str]:
    """The four source arguments as the query parameters the API expects."""
    return {param: params[argument] for argument, param, _ in LOCATION_LEVELS}


def options_for(
    param: str, list_key: str, selection: dict[str, str], session: Any = None
) -> list[str]:
    """One level's options, given the narrower selection above it."""
    items = request("locations", selection, session).get(list_key) or []
    return [item[param] for item in items if item.get(param)]


def choices(field: str, selections: dict[str, str], session: Any = None) -> list[str]:
    """Options for one cascade level, given the levels chosen so far.

    Returns [] while a level above this one is unanswered, which keeps the
    config flow on that level instead of offering a list that ignores it.
    """
    selection: dict[str, str] = {}

    for argument, param, list_key in LOCATION_LEVELS:
        if argument == field:
            return options_for(param, list_key, selection, session)

        value = selections.get(argument)
        if not value:
            return []
        selection[param] = value

    return []


def validate_location(location: dict[str, str], session: Any = None) -> None:
    """Walk the cascade and report the first argument that is unknown.

    Returns without raising if every level matches, which means the request
    failed for another reason.
    """
    selection: dict[str, str] = {}

    for argument, param, list_key in LOCATION_LEVELS:
        try:
            options = options_for(param, list_key, selection, session)
        except Exception:
            # The cascade itself is unreachable, so it cannot tell us anything -
            # leave the original error to the caller.
            return

        value = location[param]
        match = next((o for o in options if o.lower() == value.lower()), None)

        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(argument, value, options)

        selection[param] = match


class KiedySmieciRetriever(RetrieverFunc):
    """Fetch the schedule for the address in ``source.params``.

    A wrong address is not reported as such: the API answers "not found" the
    same way it answers a genuine outage, so a failure is re-walked through the
    cascade to name the argument actually at fault.
    """

    def __call__(self, source: Any) -> dict[str, Any]:
        location = location_params(source.params)
        try:
            return request("terms", location, source.session)
        except Exception:
            validate_location(location, source.session)
            raise


class KiedySmieciParser(Parser["list[dict[str, Any]]"]):
    """Pick the schedule rows out of the unwrapped ``terms`` payload."""

    def __call__(self, data: Any, source: Any = None) -> "list[dict[str, Any]]":
        return data.get("listaTerminow") or []
