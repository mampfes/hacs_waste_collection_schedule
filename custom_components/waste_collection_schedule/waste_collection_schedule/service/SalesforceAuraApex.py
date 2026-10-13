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

The host sends its leaf certificate without the issuing intermediate, so no
default trust store can build a chain to it. :func:`ca_bundle` completes
certifi's roots with the missing intermediate instead of disabling
verification.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import certifi

from waste_collection_schedule import response_shape
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_bundles: dict[str, str] = {}


def ca_bundle(extra_pem: str) -> str:
    """Path of a CA bundle: certifi's roots plus ``extra_pem`` (a PEM text).

    Written once per process to a temp file and reused.
    """
    key = hashlib.sha1(extra_pem.encode("ascii")).hexdigest()
    path = _bundles.get(key)
    if path is not None and os.path.exists(path):
        return path
    with open(certifi.where(), encoding="ascii") as f:
        roots = f.read()
    fd, path = tempfile.mkstemp(prefix="wcs_ca_", suffix=".pem")
    with os.fdopen(fd, "w", encoding="ascii") as f:
        f.write(roots)
        f.write("\n")
        f.write(extra_pem)
    _bundles[key] = path
    return path


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
        ca_certs: PEM text of an intermediate certificate the host does not
            send, trusted on top of certifi's roots.
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
        ca_certs: str | None = None,
        timeout: int = 30,
    ):
        self.host = host
        self.app = app
        self.page_uri = page_uri
        self.classname = classname
        self.method = method
        self.params = params
        self.base_path = base_path
        self.ca_certs = ca_certs
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        verify: Any = ca_bundle(self.ca_certs) if self.ca_certs else True
        base = f"https://{self.host}{self.base_path}"
        boot = source.session.get(
            f"{base}/c/{self.app}.app",
            params={"aura.format": "JSON", "aura.formatAdapter": "LIGHTNING_OUT"},
            verify=verify,
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
        response = source.session.post(
            f"{base}/aura",
            params={"r": 2, "aura.ApexAction.execute": 1},
            data={
                "message": json.dumps({"actions": [action]}),
                "aura.context": json.dumps(aura_context),
                "aura.pageURI": self.page_uri,
                "aura.token": "null",
            },
            verify=verify,
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
