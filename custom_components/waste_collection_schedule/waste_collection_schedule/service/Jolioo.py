"""Jolioo mobile-app API (``app.jolioo.com/api/mobile-app``), Austrian municipality apps.

Several Austrian municipalities and associations (Gänserndorf, the Lipizzanerheimat
communities around Köflach and Voitsberg) publish their waste calendar through a
white-label app built on Jolioo. Each app has its own key and secret, which ship
inside the app, and every call is signed the way the app signs it::

    POST /api/mobile-app/<endpoint>      body: key=value&key=value
    APIKEY: <app key>
    APIHASH: sha1("<app secret>@api/mobile-app/<endpoint>@<body>")
    Authorization: Basic <the vendor's shared client login>

The answer is ``{"success": true, "data": ...}``. The calendar is two calls:

* ``garbagecalendarindexwithstreets`` lists the app's calendars and, per street,
  the calendars that serve it (``street_structure`` with
  ``garbage_calendars_available``);
* ``garbagecalendar`` answers one calendar's ``labels`` (the waste types) and
  ``items`` (a date each, ``DD.MM.YYYY``, with the id of its label).

:func:`call` declares a signed call as a
:class:`~waste_collection_schedule.retrievers.Request` (usable as a
:class:`~waste_collection_schedule.retrievers.Lookup` request or a ``before`` step)
and :class:`CalendarParser` reads the calendar into ``(date, waste type)`` rows.
"""

from __future__ import annotations

import base64
import datetime
import hashlib
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import Request

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API_URL = "https://app.jolioo.com/api/mobile-app/"
# The login every Jolioo app sends with its calls; it ships inside the apps.
_CLIENT_LOGIN = "mopedshop:T4P4qSur"


def call(
    key: str,
    secret: str,
    endpoint: str,
    params: Callable[..., Mapping[str, Any]] | Mapping[str, Any],
    **request: Any,
) -> Request:
    """One signed call of an app as a declared POST.

    Args:
        key: the app's ``APIKEY``.
        secret: the app's secret, the first part of the signature.
        endpoint: the call (``garbagecalendar``).
        params: the form fields; a callable is called as every
            :class:`Request` field is, with the keys of earlier steps and then
            the source params by name.
        **request: the remaining :class:`Request` arguments (``before``,
            ``timeout``, ...).
    """

    def body(*args: Any, **source_params: Any) -> str:
        fields = params(*args, **source_params) if callable(params) else params
        return "&".join(f"{name}={value}" for name, value in fields.items())

    def headers(*args: Any, **source_params: Any) -> dict[str, str]:
        payload = body(*args, **source_params)
        signature = hashlib.sha1(
            f"{secret}@api/mobile-app/{endpoint}@{payload}".encode()
        ).hexdigest()
        return {
            "Content-Type": "application/x-www-form-urlencoded",
            "APIHASH": signature,
            "APIKEY": key,
            "VERSION": "1",
            "Authorization": "Basic "
            + base64.b64encode(_CLIENT_LOGIN.encode()).decode(),
            "User-Agent": f"JoliooMobileApp-{key}",
        }

    return Request(
        f"{API_URL}{endpoint}", method="POST", data=body, headers=headers, **request
    )


class CalendarParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, waste type)`` rows from a ``garbagecalendar`` answer.

    Args:
        children_only: read only the labels that have a parent label. The apps
            that group their types under headings ("Restmüll" under "Abfall")
            also list the headings, which no item carries.
    """

    def __init__(self, *, children_only: bool = False):
        self.children_only = children_only

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        data = response.json().get("data") or {}
        labels = {
            label["garbage_label_id"]: label["garbage_label_title"]
            for label in data.get("labels", [])
            if not self.children_only
            or label.get("garbage_label_id_parent") is not None
        }
        return [
            (
                datetime.datetime.strptime(
                    item["garbage_calendar_item_date"], "%d.%m.%Y"
                ).date(),
                labels[item["garbage_label_id"]],
            )
            for item in data.get("items", [])
            if item["garbage_label_id"] in labels
        ]
