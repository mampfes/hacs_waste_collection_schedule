"""A UK council "property" bins portal (``/property/{uprn}``).

Bridgend (bridgendportal.azurewebsites.net) and Shropshire
(bins.shropshire.gov.uk) run the same portal: the page for a UPRN lists one
table row per service, its name in ``td.service-name`` and its next date in
``td.next-service`` after a label ("Next Service 01/10/2026")::

    retrieve = HttpGetRetriever(url=lambda uprn, **_: f"{SITE}/property/{uprn}")
    parse = next_service_parser()
"""

from waste_collection_schedule import date_parsers
from waste_collection_schedule.parsers import HtmlLabelledDates


def next_service_parser() -> HtmlLabelledDates:
    """``(date, service)`` rows, one per service row."""
    return HtmlLabelledDates(
        "tr:has(> td.next-service)",
        label="td.service-name a",
        date="td.next-service",
        date_pattern=r"\d{2}/\d{2}/\d{4}",
        parse_date=date_parsers.for_format("%d/%m/%Y"),
    )
