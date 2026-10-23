"""Infovision "NetDialog" citizen portals (``<council>.infovision.dk``), Danish municipalities.

Kolding and Kalundborg publish their collection days through the same Infovision
citizen portal, each with its own API host (``<council>ivapi.infovision.dk``). The
address picker of the portal ends on a page whose URL carries the address id
(``/public/address/<id>``), and one public call answers everything for it::

    GET /api/publiccitizen/container/address/active/<id>
    [{"containerType": {"description": "240 L 2-delt beholder til rest og madaffald"},
      "collectDates": [20260914, 20260928, ...]}, ...]

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
        rows: list[tuple[datetime.date, str]] = []
        for container in response.json():
            description = str(
                (container.get("containerType") or {}).get("description") or ""
            ).strip()
            for stamp in container.get("collectDates") or []:
                rows.append(
                    (
                        datetime.datetime.strptime(str(stamp), "%Y%m%d").date(),
                        description,
                    )
                )
        return rows
