"""Salesforce Aura "Apex action" call, as the Chesterfield bin checker makes it.

Chesterfield's "check bin collections" page embeds a Salesforce Lightning Out
application (``c:cbc_VE_CollectionDaysLO``) on ``myaccount.<council>.gov.uk``.
The browser's conversation is two requests:

1. GET the Lightning Out application as JSON to read the Aura configuration
   (``fwuid`` and the ``loaded`` component versions).
2. POST an ``ApexActionController/ACTION$execute`` action for an Apex class and
   method (``CBC_VE_CollectionDays.getServicesByUPRN``). The answer lists
   ``serviceUnits``; each one has ``serviceTasks`` (``taskTypeName`` is
   "Collect Domestic Refuse") whose ``serviceTaskSchedules`` carry the next
   scheduled date as a UTC timestamp.

:class:`AuraApexRetriever` is that conversation and :class:`AuraServiceUnitsParser`
reads the answer into ``(timestamp, task name)`` rows.

Chesterfield's host sends its leaf certificate without the issuing
intermediate, so no default trust store can build a chain to it. The
retriever takes a ``verify`` value for its requests; ``tls.AIA`` completes the
chain from the leaf's AIA URL (see :mod:`waste_collection_schedule.tls`).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import response_shape, tls
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response


class AuraApexRetriever(RetrieverFunc):
    """Call one Apex method through the Aura endpoint of a Lightning Out app.

    Args:
        host: the Salesforce site's host.
        app: the Lightning Out application name (``cbc_VE_CollectionDaysLO``).
        page_uri: the ``aura.pageURI`` of the embedding page.
        classname: the Apex class.
        method: the Apex method.
        params: ``callable(**source.params) -> dict``, the method's arguments.
        base_path: path prefix of the site (default ``/anonymous``).
        verify: TLS verification for both requests: ``True`` (default), a CA
            bundle path (:func:`tls.ca_bundle`), or :data:`tls.AIA` for a host
            that omits its intermediate certificate.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        host: str,
        *,
        app: str,
        page_uri: str,
        classname: str,
        method: str,
        params: Callable[..., dict[str, Any]],
        base_path: str = "/anonymous",
        verify: tls.Verify = True,
        timeout: int = 30,
    ):
        self.host = host
        self.app = app
        self.page_uri = page_uri
        self.classname = classname
        self.method = method
        self.params = params
        self.base_path = base_path
        self.verify = verify
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        base = f"https://{self.host}{self.base_path}"
        boot = tls.send(
            source.session.get,
            f"{base}/c/{self.app}.app",
            self.verify,
            params={"aura.format": "JSON", "aura.formatAdapter": "LIGHTNING_OUT"},
            timeout=self.timeout,
        )
        boot.raise_for_status()
        try:
            context = boot.json()["auraConfig"]["context"]
            fwuid = context["fwuid"]
        except (KeyError, TypeError, ValueError):
            response_shape.expect(
                False,
                source_name=response_shape.source_name(source),
                detail="Lightning Out application carries no auraConfig",
                raw=boot.text,
            )
        action = {
            "id": "4;a",
            "descriptor": "aura://ApexActionController/ACTION$execute",
            "callingDescriptor": "UNKNOWN",
            "params": {
                "namespace": "",
                "classname": self.classname,
                "method": self.method,
                "params": self.params(**source.params),
                "cacheable": False,
                "isContinuation": False,
            },
        }
        aura_context = {
            "mode": "PROD",
            "fwuid": fwuid,
            "app": f"c:{self.app}",
            "loaded": context.get("loaded", {}),
            "dn": [],
            "globals": {},
            "uad": True,
        }
        response = tls.send(
            source.session.post,
            f"{base}/aura",
            self.verify,
            params={"r": 2, "aura.ApexAction.execute": 1},
            data={
                "message": json.dumps({"actions": [action]}),
                "aura.context": json.dumps(aura_context),
                "aura.pageURI": self.page_uri,
                "aura.token": "null",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response


class AuraServiceUnitsParser(Parser["list[tuple[str, str]]"]):
    """``(next scheduled timestamp, task name)`` rows of an Apex answer.

    Reads ``returnValue.returnValue.serviceUnits``: units without a service
    task (a commercial schedule on a residential property) or without a next
    instance are skipped.
    """

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[str, str]]:
        try:
            units = response.json()["actions"][0]["returnValue"]["returnValue"][
                "serviceUnits"
            ]
        except (KeyError, IndexError, TypeError, ValueError):
            response_shape.expect(
                False,
                source_name=response_shape.source_name(source),
                detail="Apex answer carries no serviceUnits",
                raw=response.text,
            )
        rows: list[tuple[str, str]] = []
        for unit in units:
            for task in unit.get("serviceTasks") or []:
                for schedule in task.get("serviceTaskSchedules") or []:
                    stamp = (schedule.get("nextInstance") or {}).get(
                        "currentScheduledDate"
                    )
                    if stamp:
                        rows.append((stamp, str(task["taskTypeName"])))
        return rows
