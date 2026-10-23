"""Verint Cloud "empro" forms (``<council>.form.uk.empro.verintcloudservices.com``).

UK councils (Bolton, Fife, Manchester) build their bin-day lookups as Verint
Cloud forms. The browser's conversation with the form's JSON API is the same
for all of them:

1. ``GET api/citizen`` answers with an ``Authorization`` token in its *headers*.
2. Every later call is a POST that sends that token back. A reply may carry a
   fresh ``Authorization`` header, which replaces the old one for the next call.
3. A custom action (``api/custom?action=...``) takes the form's JSON envelope,
   ``{"name": <form>, "email": "", "caseid": "", ..., "data": {...}}``, and
   answers with the council's own result under ``data``.

The calls and the shape of the answers are each council's own. :class:`VerintCloudRetriever`
is the conversation, so a source declares its steps and reads the last reply::

    retrieve = VerintCloudRetriever(
        "https://example.form.uk.empro.verintcloudservices.com/",
        form="bin_calendar",
        steps=(
            VerintStep(
                "api/custom?action=get_collections&actionedby=bin_calendar&loadform=true&access=citizen&locale=en",
                data=lambda previous, uprn, **_: {"uprn": str(uprn)},
            ),
        ),
    )
    parse = parsers.JsonParser("data")
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from waste_collection_schedule import response_shape
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

AUTH_HEADER = "Authorization"
DEFAULT_AUTH_PATH = "api/citizen?archived=Y&preview=false&locale=en"


def _token(response: Response) -> str | None:
    """The reply's ``Authorization`` header, whatever its capitalisation."""
    for name, value in response.headers.items():
        if name.lower() == AUTH_HEADER.lower():
            return str(value)
    return None


class VerintStep:
    """One POST to the form's API.

    Args:
        path: the call's path under the base URL, or a ``callable(previous,
            **source.params) -> str`` for one that depends on what the previous
            reply said (an object id picked from a search). ``previous`` is the
            previous reply; for the first step it is the authentication reply.
        data: ``callable(previous, **source.params) -> dict``, the envelope's
            ``data``. ``None`` posts no body, for the calls that take everything
            in the path.
    """

    def __init__(
        self,
        path: str | Callable[..., str],
        *,
        data: Callable[..., Mapping[str, Any]] | None = None,
    ):
        self.path = path
        self.data = data


class VerintCloudRetriever(RetrieverFunc):
    """Authenticate with the form, then make each step's call; return the last reply.

    Args:
        base_url: the form's host, ``https://<council>.form.uk.empro.verintcloudservices.com/``.
        form: the form's name, sent as the envelope's ``name``.
        steps: the calls to make, in order.
        auth_path: the path that answers with the ``Authorization`` token.
        headers: extra request headers (a ``referer`` some councils check).
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        *,
        form: str,
        steps: tuple[VerintStep, ...],
        auth_path: str = DEFAULT_AUTH_PATH,
        headers: Mapping[str, str] | None = None,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.form = form
        self.steps = tuple(steps)
        self.auth_path = auth_path
        self.headers = dict(headers or {})
        self.timeout = timeout

    def _envelope(self, data: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "name": self.form,
            "email": "",
            "caseid": "",
            "xref": "",
            "xref1": "",
            "xref2": "",
            "data": dict(data),
        }

    def __call__(self, source: BaseSource) -> Response:
        session = source.session
        previous = session.get(
            urljoin(self.base_url, self.auth_path), timeout=self.timeout
        )
        previous.raise_for_status()
        token = _token(previous)
        response_shape.expect(
            bool(token),
            source_name=response_shape.source_name(source),
            detail="Verint Cloud form answered without an Authorization token",
            raw=previous.text,
        )

        params = source.params
        for step in self.steps:
            path = step.path(previous, **params) if callable(step.path) else step.path
            data = step.data(previous, **params) if step.data is not None else None
            response = session.post(
                urljoin(self.base_url, path),
                json=self._envelope(data) if data is not None else None,
                headers={
                    "accept": "application/json",
                    AUTH_HEADER: token,
                    **self.headers,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            token = _token(response) or token
            previous = response
        return previous
