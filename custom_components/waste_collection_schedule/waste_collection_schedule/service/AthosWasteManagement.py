"""Reusable pieces for the Athos "WasteManagementServlet" platform.

The wizard itself is ``retrievers.AthosWasteManagementRetriever`` (data-driven
steps) and the notice filter is ``retrievers.AthosNoticeFilter``. This module
holds what a deployment adds on top of them that is not tied to one provider.
"""

from __future__ import annotations

from typing import Any

from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple


class AthosCalendarRequired:
    """Step ``validate`` for the ``filedownload_ICAL`` step: fail clearly when
    the servlet answered with its HTML form instead of a calendar.

    The servlet does not reject an address it does not know (a street that is
    not in the village, a house number the street lacks): it answers the final
    POST with ``200`` and the address form again, which the ICS parser then
    dies on with an unrelated ``ValueError`` from deep inside the calendar
    library. A real answer is ``text/calendar`` and starts a VCALENDAR, so this
    checks for that and blames the address arguments instead.

    Usage::

        {
            "submit_action": "filedownload_ICAL",
            "fields": lambda **_: {"ApplicationName": "..."},
            "validate": AthosCalendarRequired("city", "street", "house_number"),
        }

    ``arguments`` are the source's own argument names, written exactly as in
    its ``PARAMS``; they are what the Home Assistant form highlights.
    """

    def __init__(self, *arguments: str) -> None:
        self.arguments = arguments

    def __call__(self, response: Any, source: Any) -> None:
        if "BEGIN:VCALENDAR" in response.text:
            return
        raise SourceArgumentExceptionMultiple(
            self.arguments,
            "No collection dates were found for this address. Please check "
            "the spelling of the village, street and house number (and any "
            "house number addition) against the provider's own calendar.",
        )
