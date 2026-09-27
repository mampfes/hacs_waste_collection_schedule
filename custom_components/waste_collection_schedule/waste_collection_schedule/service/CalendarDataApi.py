"""The ``/api/getCalendarData`` waste API several UK councils front (Camden,
Sheffield).

One POST per property, ``{"councilId": ..., "uprn": ...}``, answered with a
status message and the property's services, each carrying its scheduled
collections::

    {"message": "OK", "data": [{"records": [
        {"service": "Rubbish collection", "actual_scheduled_date": "2026-10-01T00:00:00Z", ...}]}]}

Wire a council with::

    retrieve = calendar_data_retriever("https://wasteservices.sheffield.gov.uk", "1")
    parse = calendar_data_parser()
    preprocess = ExplodeList("records")
    transform = JsonTransformer(date_key=scheduled_date, type_key="service", ...)
"""

from typing import Any

from waste_collection_schedule import date_parsers
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.retrievers import HttpPostRetriever

PARSE_DATE = date_parsers.for_format("%Y-%m-%d")


def calendar_data_retriever(site: str, council_id: str) -> HttpPostRetriever:
    """The calendar data of the ``uprn`` param from ``site``."""
    return HttpPostRetriever(
        url=f"{site.rstrip('/')}/api/getCalendarData",
        json=lambda uprn, **_: {"councilId": council_id, "uprn": str(uprn)},
        headers={"x-recaptcha-token": ""},
    )


def calendar_data_parser() -> JsonParser:
    """The reply's service groups; a message other than "OK" raises."""
    return JsonParser("data", expected_values={"message": "OK"})


def scheduled_date(record: "dict[str, Any]") -> str:
    """The record's scheduled date as ``YYYY-MM-DD``."""
    return (record.get("actual_scheduled_date") or "")[:10]
