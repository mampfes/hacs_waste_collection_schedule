"""Infovision "NetDialog" citizen portals (``<council>.infovision.dk``), Danish municipalities.

Kolding and Kalundborg publish their collection days through the same Infovision
citizen portal, each with its own API host (``<council>ivapi.infovision.dk``). The
address picker of the portal ends on a page whose URL carries the address id
(``/public/address/<id>``), and one public call answers everything for it::

    GET /api/publiccitizen/container/address/active/<id>
    {"chainDetailsOwn": [{"containerDetails": [
        {"containerType": {"description": "240 L 2-delt beholder til rest og madaffald"},
         "collectCalendar": [{"collectDate": 20260914}, {"collectDate": 20260928}, ...]},
        ...]}],
     "chainDetailsZero": [...], "chainDetailsUse": [...]}

The portal used to answer with a flat list of containers carrying ``collectDates``;
the parser still accepts that shape.

The call is "public" by the fixed header ``publicaccesstoken:
__NetDialogCitizenPublicAccessToken__``, which the portal's own script sends.

:func:`container_retriever` declares the call and :class:`ContainerParser` reads
the containers into ``(date, container description)`` rows, so a municipality is
its API host, the clean-up of its container wording and the map from that to waste
types::

    retrieve = container_retriever("example")
    parse = ContainerParser()
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

PUBLIC_ACCESS_TOKEN = "__NetDialogCitizenPublicAccessToken__"


def container_retriever(council: str, id_field: str = "id") -> Request:
    """The active containers of the address id in ``source.params[id_field]``."""
    return Request(
        lambda **params: (
            f"https://{council}ivapi.infovision.dk/api/publiccitizen/"
            f"container/address/active/{str(params[id_field]).strip()}"
        ),
        headers={
            "accept": "application/json, text/plain, */*",
            "publicaccesstoken": PUBLIC_ACCESS_TOKEN,
        },
    )


class ContainerParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, container description)`` rows, one per container and collection date."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        data = response.json()
        containers: list[dict[str, Any]] = []
        if isinstance(data, dict):
            for chains in data.values():
                if isinstance(chains, list):
                    for chain in chains:
                        containers.extend(chain.get("containerDetails") or [])
        else:
            containers = data

        rows: list[tuple[datetime.date, str]] = []
        for container in containers:
            description = str(
                (container.get("containerType") or {}).get("description") or ""
            ).strip()
            stamps = container.get("collectDates") or [
                item["collectDate"]
                for item in container.get("collectCalendar") or []
                if item.get("collectDate")
            ]
            for stamp in stamps:
                rows.append(
                    (
                        datetime.datetime.strptime(str(stamp), "%Y%m%d").date(),
                        description,
                    )
                )
        return rows
