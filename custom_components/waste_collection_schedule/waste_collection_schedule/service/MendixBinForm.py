"""Mendix "bin collection information" pages (``<council>transaction.mendixcloud.com``).

Knowsley Council runs its bin-day lookup as a Mendix client application. The
browser's conversation with the Mendix runtime (``/xas/``) is:

1. ``GET link/youarebeingredirected?target=...`` mints the session cookie.
2. ``POST xas/ get_session_data`` answers the CSRF token, the cache-bust key and
   the session's objects.
3. ``executeaction`` ``Service_YouAreBeingRedirected.SUB_YouAreBeingRedirected``
   answers the page to open (``FormPath``), the enquiry object and its changes.
4. The page's JavaScript names two ``runtimeOperation`` ids (post the postcode,
   choose the address); they are read off the page.
5. The first operation lists the addresses of the postcode (each with its UPRN),
   the second answers the chosen property's ``Next<Bin>`` dates.

:class:`MendixBinFormRetriever` runs it and returns the last reply;
:class:`MendixBinFormParser` reads it into ``(date, bin name)`` rows. A council
on the same application is its base URL.
"""

from __future__ import annotations

import re
import time
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

_OPERATION_ID = re.compile(r'"config":\{"operationId":"(.+?)",')
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


class MendixBinFormRetriever(RetrieverFunc):
    """Walk the Mendix postcode and address forms; return the property's reply.

    Args:
        base_url: the application's host, ``https://<council>.mendixcloud.com/``.
        target: the ``target`` of the redirect link that opens the bin form.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        *,
        target: str = "bincollectioninformation",
        timeout: int = 30,
    ):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.target = target
        self.timeout = timeout

    def _call(
        self,
        source: BaseSource,
        csrf: str,
        counter: list[int],
        action: str,
        **payload: Any,
    ) -> dict[str, Any]:
        counter[0] += 1
        body: dict[str, Any] = {
            "action": action,
            "changes": {},
            "objects": [],
            "params": {},
            "profiledata": {},
            **payload,
        }
        response = source.session.post(
            self.base_url + "xas/",
            json=body,
            headers={
                "x-csrf-token": csrf,
                "x-mx-reqtoken": f"{int(time.time())}-{counter[0]}",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def __call__(self, source: BaseSource) -> Response:
        session = source.session
        name = response_shape.source_name(source)
        postcode = str(source.params["postcode"])
        uprn = str(source.params["uprn"]).strip().strip("0")

        session.get(
            f"{self.base_url}link/youarebeingredirected?target={self.target}",
            timeout=self.timeout,
        ).raise_for_status()
        init = session.post(
            self.base_url + "xas/",
            json={"action": "get_session_data", "params": _SESSION_PARAMS},
            timeout=self.timeout,
        )
        init.raise_for_status()
        session_data = init.json()
        csrf = session_data["csrftoken"]
        counter = [2]

        enquiry = session_data["objects"][1]
        opened = self._call(
            source,
            csrf,
            counter,
            "executeaction",
            objects=[enquiry],
            params={
                "actionname": "Service_YouAreBeingRedirected.SUB_YouAreBeingRedirected",
                "applyto": "selection",
                "guids": [enquiry["guid"]],
            },
        )

        page = session.get(
            f"{self.base_url}pages/en_US/"
            f"{opened['instructions'][0]['args']['FormPath']}",
            params={session_data["cachebust"]: ""},
            timeout=self.timeout,
        )
        page.raise_for_status()
        operation_ids = _OPERATION_ID.findall(page.text)
        response_shape.expect(
            len(operation_ids) >= 2,
            source_name=name,
            detail="Mendix bin form page names fewer than two operations",
            raw=page.text,
        )

        objects = opened["objects"]
        form_guid = objects[0]["guid"]
        changes = opened["changes"]
        changes[next(iter(changes))]["EnquiryPostcodeOrStreetName"] = {
            "value": postcode
        }
        addresses = self._call(
            source,
            csrf,
            counter,
            "runtimeOperation",
            objects=objects,
            changes=changes,
            operationId=operation_ids[0],
            params={"OS_MissedBinEnquiry": {"guid": form_guid}},
            validationGuids=[form_guid],
        )

        chosen = next(
            (
                (guid, change)
                for guid, change in addresses["changes"].items()
                if "UPRN" in change
                and str(change["UPRN"]["value"]).strip().strip("0") == uprn
            ),
            None,
        )
        if chosen is None:
            raise SourceArgumentNotFound("uprn", source.params["uprn"])
        guid, change = chosen

        objects = [*objects, next(o for o in addresses["objects"] if o["guid"] == guid)]
        changes = dict(changes)
        changes[next(iter(changes))]["ShowAddressResults"] = {"value": True}
        changes[guid] = change
        return session.post(
            self.base_url + "xas/",
            json={
                "action": "runtimeOperation",
                "changes": changes,
                "objects": objects,
                "params": {"Generic_Address": {"guid": guid}},
                "profiledata": {},
                "operationId": operation_ids[1],
                "validationGuids": [form_guid],
            },
            headers={
                "x-csrf-token": csrf,
                "x-mx-reqtoken": f"{int(time.time())}-{counter[0] + 1}",
            },
            timeout=self.timeout,
        )


class MendixBinFormParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, bin name)`` rows from the ``Next<Bin>`` attributes of the reply.

    The dates read "Tuesday 07/01/2025".
    """

    _parse_date = date_parsers.for_format("%A %d/%m/%Y")

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        changes: Mapping[str, Mapping[str, Any]] = response.json().get("changes") or {}
        return [
            (self._parse_date(value["value"]), key.removeprefix("Next"))
            for change in changes.values()
            for key, value in change.items()
            if key.startswith("Next") and isinstance(value, dict) and value.get("value")
        ]
