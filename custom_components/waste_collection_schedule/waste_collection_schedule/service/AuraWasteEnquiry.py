"""Salesforce Aura "waste collection enquiry" flow, UK councils on the Alloy community portals.

Cotswold, Forest of Dean and West Oxfordshire run the same Salesforce community
(``community.<council>.gov.uk/s/waste-collection-enquiry``): a Salesforce Flow
(``WebFormAlloyWasteCollectionEnquiry``) driven through the Aura endpoint
``/s/sfsites/aura``. The browser's conversation, which is also the only way in:

1. GET the enquiry page and read the Aura configuration (``fwuid`` and the
   ``loaded`` component versions) out of ``var auraConfig = ...``.
2. ``startFlow`` with the council's ``vClientCode`` answers the flow's
   serialized state.
3. A ``lookup`` of the address (type-ahead on ``Case.Property__c``) answers the
   matching properties; the chosen property's id and name go back to the flow.
4. ``navigateFlow`` NEXT with the property, then ``CONTINUE_AFTER_COMMIT``
   twice. The last answer carries the schedule as a JSON table in one of the
   flow screen's inputs: one row per bin, ``col1`` its name, ``col2`` the next
   date ("Tue, 20 August", "Today", "Tomorrow").

:class:`AuraWasteEnquiryRetriever` is that conversation and
:class:`AuraWasteTableParser` reads the table into ``(date, bin)`` rows, so a
council is its host, its ``vClientCode`` and the map from its bin names to
waste types::

    retrieve = AuraWasteEnquiryRetriever("community.example.gov.uk", client_code="EXC")
    parse = AuraWasteTableParser()
    transform = RowTransformer(type_value_map={...})
"""

from __future__ import annotations

import datetime
import json
import re
from typing import TYPE_CHECKING, Any

from waste_collection_schedule import date_parsers, response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

_AURA_CONFIG = re.compile(r"var\s+auraConfig\s*=\s*(.*?),\n")
_PAGE_URI = "/s/waste-collection-enquiry"
_FLOW = "WebFormAlloyWasteCollectionEnquiry"
_NEXT_DATE = date_parsers.next_weekday("%a, %d %B")


def _normalise(address: str | None) -> str:
    return re.sub(r"[ .,]", "", address or "").lower()


class AuraWasteEnquiryRetriever(RetrieverFunc):
    """Walk the enquiry flow for the configured address; return the last answer.

    Args:
        host: the community portal's host (``community.<council>.gov.uk``).
        client_code: the council's ``vClientCode``.
        address: the ``source.params`` field holding the full address, as the
            portal's own look-up spells it.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        host: str,
        *,
        client_code: str,
        address: str = "address",
        timeout: int = 30,
    ):
        self.host = host
        self.client_code = client_code
        self.address = address
        self.timeout = timeout

    def _context(self, source: BaseSource) -> str:
        page = source.session.get(
            f"https://{self.host}{_PAGE_URI}", timeout=self.timeout
        )
        page.raise_for_status()
        match = _AURA_CONFIG.search(page.text)
        response_shape.expect(
            match is not None,
            source_name=response_shape.source_name(source),
            detail="enquiry page carries no auraConfig",
            raw=page.text,
        )
        context = json.loads(match.group(1))["context"]  # type: ignore[union-attr]
        return json.dumps(
            {
                "mode": "PROD",
                "fwuid": context["fwuid"],
                "app": "siteforce:communityApp",
                "loaded": context["loaded"],
                "dn": [],
                "globals": {},
                "uad": False,
            }
        )

    def _call(
        self,
        source: BaseSource,
        aura_context: str,
        counter: int,
        method: str,
        action: dict[str, Any],
    ) -> Response:
        response = source.session.post(
            f"https://{self.host}/s/sfsites/aura",
            params={"r": counter, method: 1},
            data={
                "message": json.dumps({"actions": [action]}),
                "aura.context": aura_context,
                "aura.pageURI": _PAGE_URI,
                "aura.token": "null",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    @staticmethod
    def _return_value(response: Response) -> dict[str, Any]:
        return response.json()["actions"][0]["returnValue"]

    def __call__(self, source: BaseSource) -> Response:
        wanted = str(source.params[self.address])
        aura = self._context(source)

        started = self._call(
            source,
            aura,
            5,
            "aura.FlowRuntimeConnect.startFlow",
            {
                "id": "85;a",
                "descriptor": "aura://FlowRuntimeConnectController/ACTION$startFlow",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "flowDevName": _FLOW,
                    "arguments": json.dumps(
                        [
                            {
                                "name": "vClientCode",
                                "type": "String",
                                "supportsRecordId": False,
                                "value": self.client_code,
                            }
                        ],
                        separators=(",", ":"),
                    ),
                    "enableTrace": False,
                    "enableRollbackMode": False,
                    "debugAsUserId": "",
                    "useLatestSubflow": False,
                },
            },
        )
        state = self._return_value(started)["response"]["serializedEncodedState"]

        found = self._call(
            source,
            aura,
            1,
            "aura.LookupController.lookupaura.Lookup.lookup",
            {
                "id": "89;a",
                "descriptor": "aura://LookupController/ACTION$lookup",
                "callingDescriptor": "UNKNOWN",
                "params": {
                    "objectApiName": "Case",
                    "fieldApiName": "Property__c",
                    "pageParam": 1,
                    "pageSize": 25,
                    "q": wanted,
                    "searchType": "TypeAhead",
                    "targetApiName": "Property__c",
                    "body": {
                        "sourceRecord": {"apiName": "Case", "fields": {"Id": None}}
                    },
                },
            },
        )
        properties = self._return_value(found)["lookupResults"]["Property__c"][
            "records"
        ]
        names = {
            p["fields"]["Name"]["value"]
            for p in properties
            if p["fields"]["Name"]["value"]
        }
        match = next(
            (
                p
                for p in properties
                if _normalise(p["fields"]["Name"]["value"]) == _normalise(wanted)
            ),
            None,
        )
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                self.address, wanted, sorted(names)
            )
        property_id = match["id"]
        property_name = match["fields"]["Name"]["value"]

        self._call(
            source,
            aura,
            25,
            "aura.RecordUi.getRecordWithFields",
            {
                "id": "114;a",
                "descriptor": "aura://RecordUiController/ACTION$getRecordWithFields",
                "callingDescriptor": "UNKNOWN",
                "params": {"recordId": property_id, "fields": ["Property__c.Name"]},
            },
        )

        def navigate(counter: int, action_id: str, request: dict[str, Any]) -> Response:
            return self._call(
                source,
                aura,
                counter,
                "aura.FlowRuntimeConnect.navigateFlow",
                {
                    "id": action_id,
                    "descriptor": "aura://FlowRuntimeConnectController/ACTION$navigateFlow",
                    "callingDescriptor": "UNKNOWN",
                    "params": {"request": request},
                },
            )

        response = navigate(
            26,
            "123;a",
            {
                "action": "NEXT",
                "serializedState": state,
                "fields": [
                    {
                        "field": "Property.recordId",
                        "value": property_id,
                        "isVisible": True,
                    },
                    {
                        "field": "Property.recordIds",
                        "value": [property_id],
                        "isVisible": True,
                    },
                    {
                        "field": "Property.recordName",
                        "value": property_name,
                        "isVisible": True,
                    },
                ],
                "uiElementVisited": True,
                "enableTrace": False,
                "lcErrors": {},
            },
        )
        for counter, action_id in ((27, "125;a"), (28, "127;a")):
            state = self._return_value(response)["response"]["serializedEncodedState"]
            response = navigate(
                counter,
                action_id,
                {
                    "action": "CONTINUE_AFTER_COMMIT",
                    "serializedState": state,
                    "fields": [],
                    "uiElementVisited": True,
                    "enableTrace": False,
                },
            )
        return response


class AuraWasteTableParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, bin name)`` rows from the flow's final screen."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        try:
            value = response.json()["actions"][0]["returnValue"]["response"]["fields"][
                1
            ]["inputs"][3]["value"]
            table = json.loads(value)
        except (KeyError, IndexError, TypeError, ValueError):
            response_shape.expect(
                False,
                source_name=response_shape.source_name(source),
                detail="enquiry flow's final screen carries no schedule table",
                raw=response.text,
            )
        today = datetime.date.today()
        rows: list[tuple[datetime.date, str]] = []
        for row in table:
            text = str(row["col2"]).strip()
            if text.lower() == "today":
                day: datetime.date | None = today
            elif text.lower() == "tomorrow":
                day = today + datetime.timedelta(days=1)
            else:
                try:
                    day = _NEXT_DATE(text)
                except ValueError:
                    day = None
            if day is not None:
                rows.append((day, str(row["col1"])))
        return rows
