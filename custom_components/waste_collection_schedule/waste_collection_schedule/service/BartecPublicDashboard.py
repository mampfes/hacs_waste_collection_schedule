"""Bartec Municipal "Public Dashboard" collection calendars.

Several UK councils publish their bin days through the same Bartec Municipal
Razor page (``bins.<council>/PublicDashboard``, or an ``/Embeddable/...``
variant of it). The page takes a postcode and a UPRN and renders both the
postcode's premises and the chosen property's appointments as JSON embedded in
its scripts::

    "dataSource": ejs.data.DataUtil.parse.isJson([{"UPRN": ..., "Premises": ...}])
    "dataSource": ejs.data.DataUtil.parse.isJson([{"Subject": "Rubbish",
                                                   "StartTime": "2026-07-02T00:00:00"}])

One GET for the anti-forgery token and one POST to the ``SelectPrem`` handler
are enough: the handler takes the postcode and the UPRN together, so the
page's own postcode-search step (``SearchPostcode``) can be skipped.

    retrieve  = BartecDashboardRetriever("https://bins.highpeak.gov.uk/PublicDashboard")
    parse     = BartecDashboardParser()
    transform = JsonTransformer(date_key="date", type_key="type", ...)
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import LookupChainRetriever, Response

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_TOKEN = re.compile(
    r"""name=["']__RequestVerificationToken["'][^>]*value=["']([^"']+)"""
)
_DATA_SOURCE = "ejs.data.DataUtil.parse.isJson("


class _VerificationToken:
    """``LookupChainRetriever`` step: the page's anti-forgery token."""

    def __init__(self, url: str):
        self.url = url

    def __call__(self, source: BaseSource, keys: tuple) -> str:
        response = source.session.get(self.url, timeout=30)
        response.raise_for_status()
        match = _TOKEN.search(response.text)
        if match is None:
            raise ValueError(f"No __RequestVerificationToken on {self.url}")
        return match.group(1)


class BartecDashboardRetriever(LookupChainRetriever):
    """GET the dashboard's token, then POST the property to ``SelectPrem``.

    Args:
        url: the dashboard page (``https://bins.<council>/PublicDashboard``).
        postcode / uprn: the ``source.params`` fields holding the address.
    """

    def __init__(self, url: str, *, postcode: str = "postcode", uprn: str = "uprn"):
        self.postcode = postcode
        self.uprn = uprn
        super().__init__(
            steps=(_VerificationToken(url),),
            url=url,
            method="POST",
            params=lambda *_, **__: {"handler": "SelectPrem"},
            data=self._form,
            raise_for_status=True,
        )

    def _form(self, token: str, **params: Any) -> dict[str, str]:
        return {
            "__RequestVerificationToken": token,
            "SelectedPostcode": str(params[self.postcode]).strip().upper(),
            "SelectedPremises": str(params[self.uprn]).strip(),
        }


def data_sources(html: str) -> list[list[Any]]:
    """Every JSON array the page embeds as a ``dataSource``, in page order."""
    decoder = json.JSONDecoder()
    found: list[list[Any]] = []
    start = html.find(_DATA_SOURCE)
    while start != -1:
        try:
            data, _ = decoder.raw_decode(html, start + len(_DATA_SOURCE))
        except ValueError:
            data = None
        if isinstance(data, list):
            found.append(data)
        start = html.find(_DATA_SOURCE, start + 1)
    return found


def _block(blocks: list[list[Any]], *keys: str) -> list[dict[str, Any]]:
    """The first block whose rows carry all of ``keys``."""
    for block in blocks:
        if block and isinstance(block[0], dict) and all(k in block[0] for k in keys):
            return block
    return []


def _uprn(value: Any) -> str:
    """A UPRN as the page and a user write it: digits, no ``.0``."""
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()


class BartecDashboardParser(Parser["list[dict[str, Any]]"]):
    """One ``{"date", "type"}`` record per appointment, each listed once.

    A postcode the dashboard does not know renders no premises, which is
    reported against the postcode. A UPRN that is not among the postcode's
    premises renders no appointments, which is reported against the UPRN with
    the premises offered as suggestions.

    Args:
        postcode / uprn: the ``source.params`` fields to blame.
    """

    def __init__(self, *, postcode: str = "postcode", uprn: str = "uprn"):
        self.postcode = postcode
        self.uprn = uprn

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        params = source.params if source is not None else {}
        blocks = data_sources(response.text)
        appointments = _block(blocks, "Subject", "StartTime")
        if not appointments:
            premises = _block(blocks, "Premises", "UPRN")
            if not premises:
                raise SourceArgumentNotFound(self.postcode, params.get(self.postcode))
            wanted = _uprn(params.get(self.uprn))
            if wanted not in {_uprn(row["UPRN"]) for row in premises}:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.uprn,
                    params.get(self.uprn),
                    [
                        f"{row['Premises']} (UPRN {_uprn(row['UPRN'])})"
                        for row in premises
                    ],
                )
            return []

        records: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for row in appointments:
            day, subject = str(row.get("StartTime") or "")[:10], row.get("Subject")
            if not day or not subject or (day, subject) in seen:
                continue
            seen.add((day, subject))
            records.append({"date": day, "type": subject})
        return records
