"""Jadu "apiserver" JSON-RPC endpoint (``/apiserver/ajaxlibrary``), UK councils.

Councils on the Jadu CMS expose their own back-office calls to the browser
through one JSON-RPC 2.0 endpoint, ``https://<council>/apiserver/ajaxlibrary``.
The envelope is the same everywhere (``jsonrpc``, ``id``, ``method``,
``params``, and the answer under ``result``); the *methods* are each council's
own (``Breckland.Whitespace.JointWasteAPI.GetBinCollectionsByUprn``,
``stc.waste.collections.getDates``) and so are the shapes of their results.

:func:`rpc` declares one such call as a :class:`~waste_collection_schedule.retrievers.Request`,
so a source is its method names and the reading of the results::

    retrieve = rpc(
        "https://www.example.gov.uk/apiserver/ajaxlibrary",
        "Example.Waste.GetCollections",
        lambda uprn, **_: {"uprn": str(uprn)},
    )
    parse = parsers.JsonParser("result")

The call also works as a :class:`~waste_collection_schedule.retrievers.Lookup`
request (``Lookup(rpc(...), pick=...)``) and as a step ``before`` another call.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from waste_collection_schedule.retrievers import Request


def rpc(
    url: str,
    method: str,
    params: Callable[..., Mapping[str, Any]] | Mapping[str, Any],
    *,
    request_id: str = "1",
    **request: Any,
) -> Request:
    """One JSON-RPC call to ``url`` as a declared POST.

    Args:
        url: the council's ``/apiserver/ajaxlibrary`` URL.
        method: the council's own method name.
        params: the call's ``params``; a callable is called as every other
            :class:`Request` field is, with the keys resolved by earlier steps
            and then the source params by name.
        request_id: the JSON-RPC ``id``, which the service echoes back.
        **request: the remaining :class:`Request` arguments (``headers``,
            ``before``, ``timeout``, ...).
    """

    def body(*args: Any, **source_params: Any) -> dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params(*args, **source_params)
            if callable(params)
            else dict(params),
        }

    return Request(url, method="POST", json=body, **request)
