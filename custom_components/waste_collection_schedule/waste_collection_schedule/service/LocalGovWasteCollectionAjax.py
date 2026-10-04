"""LocalGov Drupal's Waste Collection module, as one AJAX form (UK councils).

Where the sibling :mod:`LocalGovWasteCollection` serves ``/find`` and
``/view/<uprn>`` pages, Rochford keeps the module's two steps on one page, as a
Drupal AJAX form (``waste_collection_block_ajax_form``)::

    GET  {page}                          the form, with its ``form_build_id``
    POST {page}?_wrapper_format=drupal_ajax&ajax_form=1
         postcode + op=Find              an ``insert`` command carrying the
                                         address ``<select name="uprn">`` and a
                                         rotated ``form_build_id``
    POST the same URL
         postcode + uprn + op=View collection days
                                         an ``insert`` command carrying the
                                         schedule, ``.waste-collection__day``

The ``<option value>`` of the address picker is the ward code and UPRN joined by
a hyphen. :class:`AjaxCollectionDaysParser` unwraps the command list and reads
the schedule with the sibling module's :class:`CollectionDaysParser`.
"""

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import (
    Lookup,
    LookupChainRetriever,
    Request,
)
from waste_collection_schedule.service.LocalGovWasteCollection import (
    CollectionDaysParser,
)

if TYPE_CHECKING:
    import datetime

    from waste_collection_schedule.base_source import BaseSource

_FORM_ID = "waste_collection_block_ajax_form"
_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def _insert_html(response: Any) -> str:
    """The HTML of the reply's first ``insert`` command."""
    for command in response.json():
        if isinstance(command, dict) and command.get("command") == "insert":
            return str(command.get("data") or "")
    return ""


def _build_id(html: str) -> str | None:
    field = BeautifulSoup(html, "html.parser").find("input", {"name": "form_build_id"})
    value = field.get("value") if field is not None else None
    return value if isinstance(value, str) else None


def ajax_form_retriever(
    page: str, postcode: str = "postcode", uprn: str = "uprn"
) -> LookupChainRetriever:
    """The schedule of the ``uprn`` param, in the ``postcode`` param's list."""
    ajax = f"{page}?_wrapper_format=drupal_ajax&ajax_form=1"
    headers = {**_HEADERS, "Referer": page}

    def _form_build_id(response: Any, *keys: Any, **_: Any) -> str:
        found = _build_id(response.text)
        if found is None:
            response_shape.expect(
                False,
                source_name="LocalGov waste collection",
                detail="bin collection page carries no form_build_id",
                raw=response.text,
            )
            raise ValueError("Could not find form_build_id on the bin collection page")
        return found

    def _pick(response: Any, *keys: Any, **params: Any) -> str:
        """Check the address against the picker; the next form's build id."""
        html = _insert_html(response)
        select = BeautifulSoup(html, "html.parser").find("select", {"name": uprn})
        options = (
            [
                str(option.get("value"))
                for option in select.find_all("option")
                if option.get("value")
            ]
            if select is not None
            else []
        )
        if not options:
            raise SourceArgumentNotFound(postcode, params[postcode])
        if str(params[uprn]).strip() not in options:
            raise SourceArgumentNotFoundWithSuggestions(uprn, params[uprn], options)
        found = _build_id(html)
        if found is None:
            raise ValueError("Could not find form_build_id in the address reply")
        return found

    return LookupChainRetriever(
        steps=(
            Lookup(Request(page, headers=headers), pick=_form_build_id),
            Lookup(
                Request(
                    ajax,
                    method="POST",
                    headers=headers,
                    data=lambda form_build_id, **params: {
                        "postcode": str(params[postcode]).strip().upper(),
                        "op": "Find",
                        "form_build_id": form_build_id,
                        "form_id": _FORM_ID,
                        "_triggering_element_name": "op",
                        "_triggering_element_value": "Find",
                        "_drupal_ajax": "1",
                    },
                ),
                pick=_pick,
            ),
        ),
        url=ajax,
        method="POST",
        headers=headers,
        data=lambda _first, build_id, **params: {
            "postcode": str(params[postcode]).strip().upper(),
            "uprn": str(params[uprn]).strip(),
            "op": "View collection days",
            "form_build_id": build_id,
            "form_id": _FORM_ID,
            "_triggering_element_name": "op",
            "_triggering_element_value": "View collection days",
            "_drupal_ajax": "1",
        },
        raise_for_status=True,
    )


class _Html:
    """The unwrapped schedule page, shaped like the response a parser reads."""

    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


class AjaxCollectionDaysParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, type)`` rows from the schedule an AJAX reply inserts."""

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        response.raise_for_status()
        return CollectionDaysParser()(_Html(_insert_html(response)), source)
