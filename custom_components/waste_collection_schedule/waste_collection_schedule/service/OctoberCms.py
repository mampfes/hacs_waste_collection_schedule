"""OctoberCMS AJAX framework handlers (``X-October-Request-Handler``), as sites use them.

OctoberCMS pages update themselves through a form post that names a server-side
*handler* and the page *partials* it wants back::

    POST /page
    X-October-Request-Handler: onSearch
    X-October-Request-Partials: ajax/results
    X-Requested-With: XMLHttpRequest

    -> {"ajax\\/results": "<div>...</div>"}        (or {".results": "..."})

The answer is JSON whose key is the partial's name, or the CSS selector the page
maps it to, and whose value is the partial's HTML. The handlers keep their state in
the session (a selected district narrows the next handler's street list), so a
source is a chain of such posts on one session.

:func:`handler` declares one post as a :class:`~waste_collection_schedule.retrievers.Request`
(usable as a :class:`~waste_collection_schedule.retrievers.Lookup` request or a
``before`` step) and :func:`partial_html` reads the HTML out of the answer::

    retrieve = handler(URL, "onSearch", "ajax/results", {"street": "Fő utca"})
    parse = parsers.HtmlParser("tr", from_json_key="ajax/results")
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from waste_collection_schedule.retrievers import Request


def handler(
    url: str,
    name: str,
    partial: str,
    data: Callable[..., Mapping[str, Any]] | Mapping[str, Any],
    **request: Any,
) -> Request:
    """One OctoberCMS handler call as a declared POST.

    Args:
        url: the page the handler belongs to.
        name: the handler (``onSearch``).
        partial: the partial to ask for (``ajax/results``).
        data: the form fields; a callable is called as every :class:`Request`
            field is, with the keys of earlier steps and then the params.
        **request: the remaining :class:`Request` arguments (``raise_for_status``,
            ``timeout``, ...).
    """
    return Request(
        url,
        method="POST",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-October-Request-Handler": name,
            "X-October-Request-Partials": partial,
            "X-Requested-With": "XMLHttpRequest",
        },
        **request,
    )


def partial_html(response: Any, *keys: str) -> str:
    """The HTML of the first of ``keys`` the answer carries, or ``""``."""
    answer = response.json()
    for key in keys:
        if answer.get(key) is not None:
            return str(answer[key])
    return ""
