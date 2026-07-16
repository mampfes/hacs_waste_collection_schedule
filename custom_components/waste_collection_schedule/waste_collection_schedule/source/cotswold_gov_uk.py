import json
import logging
import re
from datetime import date, datetime

import requests
import urllib3
from dateutil.parser import parse
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
)

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# This line suppresses the InsecureRequestWarning when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)

TITLE = "Cotswold District Council"
DESCRIPTION = "Source for Cotswold District Council, UK."
URL = "https://www.cotswold.gov.uk/"
COUNTRY = "uk"

TEST_CASES = {
    "Parsons Piece, 1 Glebe Lane, Kemble, Cirencester": {
        "address": "PARSONS PIECE, 1 GLEBE LANE, KEMBLE, CIRENCESTER, GL7 6BD"
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to the Cotswold District Council waste collection enquiry page "
        "(https://community.cotswold.gov.uk/s/waste-collection-enquiry) and "
        "start typing your postcode or street name into the address lookup. "
        "Select your property from the autocomplete suggestions and use the "
        "full address string exactly as it appears (e.g. "
        "'10 HAVEN HILL, CIRENCESTER, GL7 1BN')."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {"address": "Address"},
}

PARAM_DESCRIPTIONS = {
    "en": {
        "address": (
            "The full address string as returned by the lookup on the "
            "Cotswold District Council waste collection enquiry page."
        ),
    },
}

ICON_MAP = {
    "bin": Icons.ORGANIC,
    "refuse": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "caddy": Icons.BIO_KITCHEN,
    "box": Icons.RECYCLING,
    "garden": Icons.GARDEN,
}

REGEX_AURA_CONFIG = re.compile(r"var\s+auraConfig\s*=\s*(.*?),\n")

API_URL = "https://community.cotswold.gov.uk/s/sfsites/aura"
SEARCH_PAGE = "https://community.cotswold.gov.uk/s/waste-collection-enquiry"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class Source:
    def __init__(self, address: str):
        self._address: str = address
        self._session = requests.Session()

    @staticmethod
    def _parse_date(date_str: str) -> date:
        if date_str.lower() == "today":
            return date.today()
        if date_str.lower() == "tomorrow":
            return date.today().replace(day=date.today().day + 1)

        # Tue, 20 August
        return parse(date_str, default=datetime.now()).date()

    def _init_connection(self):
        self._session = requests.Session()
        r = self._session.get(SEARCH_PAGE, verify=False, headers=HEADERS)
        r.raise_for_status()
        aura_regex = REGEX_AURA_CONFIG.search(r.text, re.MULTILINE)

        if not aura_regex:
            raise Exception("Could not find aura config")
        json_data = json.loads(aura_regex.group(1))
        fwuid = json_data["context"]["fwuid"]
        loaded = json_data["context"]["loaded"]
        self._aura_context = json.dumps(
            {
                "mode": "PROD",
                "fwuid": fwuid,
                "app": "siteforce:communityApp",
                "loaded": loaded,
                "dn": [],
                "globals": {},
                "uad": False,
            }
        )

    def _request(
        self, r: int, aura_method: str, message: str | dict
    ) -> requests.Response:
        if isinstance(message, dict):
            message = json.dumps(message)
        response = self._session.post(
            API_URL,
            params={
                "r": r,
                aura_method: 1,
            },
            data={
                "message": message,
                "aura.context": self._aura_context,
                "aura.pageURI": "/s/waste-collection-enquiry",
                "aura.token": "null",
            },
            verify=False,
            headers=HEADERS,
        )
        response.raise_for_status()
        return response

    def _match_address(self, address: str | None) -> bool:
        if address is None:
            return False
        return self._address.lower().replace(" ", "").replace(".", "").replace(
            ",", ""
        ) == address.lower().replace(" ", "").replace(".", "").replace(",", "")

    def fetch(self) -> list[Collection]:
        self._init_connection()
        entries = []
        message1 = {
            "actions": [
                {
                    "id": "85;a",
                    "descriptor": "aura://FlowRuntimeConnectController/ACTION$startFlow",
                    "callingDescriptor": "UNKNOWN",
                    "params": {
                        "flowDevName": "WebFormAlloyWasteCollectionEnquiry",
                        "arguments": '[{"name":"vClientCode","type":"String","supportsRecordId":false,"value":"CDC"}]',
                        "enableTrace": False,
                        "enableRollbackMode": False,
                        "debugAsUserId": "",
                        "useLatestSubflow": False,
                    },
                }
            ]
        }
        r = self._request(5, "aura.FlowRuntimeConnect.startFlow", message1)
        serialized_state = r.json()["actions"][0]["returnValue"]["response"][
            "serializedEncodedState"
        ]

        message2 = {
            "actions": [
                {
                    "id": "89;a",
                    "descriptor": "aura://LookupController/ACTION$lookup",
                    "callingDescriptor": "UNKNOWN",
                    "params": {
                        "objectApiName": "Case",
                        "fieldApiName": "Property__c",
                        "pageParam": 1,
                        "pageSize": 25,
                        "q": self._address,
                        "searchType": "TypeAhead",
                        "targetApiName": "Property__c",
                        "body": {
                            "sourceRecord": {"apiName": "Case", "fields": {"Id": None}}
                        },
                    },
                }
            ]
        }
        r = self._request(1, "aura.LookupController.lookupaura.Lookup.lookup", message2)

        addresses = r.json()["actions"][0]["returnValue"]["lookupResults"][
            "Property__c"
        ]["records"]
        address_id = None
        address_name = None
        address_set = set()
        for address in addresses:
            potential_address = address["fields"]["Name"]["value"]
            address_set.add(potential_address)
            if self._match_address(potential_address):
                address_id = address["id"]
                address_name = potential_address
                break
        address_set -= {None, ""}
        if not address_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "address",
                self._address,
                address_set,
            )

        message3 = {
            "actions": [
                {
                    "id": "114;a",
                    "descriptor": "aura://RecordUiController/ACTION$getRecordWithFields",
                    "callingDescriptor": "UNKNOWN",
                    "params": {"recordId": address_id, "fields": ["Property__c.Name"]},
                }
            ]
        }
        r = self._request(25, "aura.RecordUi.getRecordWithFields", message3)

        message4 = {
            "actions": [
                {
                    "id": "123;a",
                    "descriptor": "aura://FlowRuntimeConnectController/ACTION$navigateFlow",
                    "callingDescriptor": "UNKNOWN",
                    "params": {
                        "request": {
                            "action": "NEXT",
                            "serializedState": serialized_state,
                            "fields": [
                                {
                                    "field": "Property.recordId",
                                    "value": address_id,
                                    "isVisible": True,
                                },
                                {
                                    "field": "Property.recordIds",
                                    "value": [address_id],
                                    "isVisible": True,
                                },
                                {
                                    "field": "Property.recordName",
                                    "value": address_name,
                                    "isVisible": True,
                                },
                            ],
                            "uiElementVisited": True,
                            "enableTrace": False,
                            "lcErrors": {},
                        }
                    },
                }
            ]
        }

        r = self._request(26, "aura.FlowRuntimeConnect.navigateFlow", message4)
        serialized_state = r.json()["actions"][0]["returnValue"]["response"][
            "serializedEncodedState"
        ]

        message5 = {
            "actions": [
                {
                    "id": "125;a",
                    "descriptor": "aura://FlowRuntimeConnectController/ACTION$navigateFlow",
                    "callingDescriptor": "UNKNOWN",
                    "params": {
                        "request": {
                            "action": "CONTINUE_AFTER_COMMIT",
                            "serializedState": serialized_state,
                            "fields": [],
                            "uiElementVisited": True,
                            "enableTrace": False,
                        }
                    },
                }
            ]
        }

        r = self._request(27, "aura.FlowRuntimeConnect.navigateFlow", message5)
        serialized_state = r.json()["actions"][0]["returnValue"]["response"][
            "serializedEncodedState"
        ]

        message6 = {
            "actions": [
                {
                    "id": "127;a",
                    "descriptor": "aura://FlowRuntimeConnectController/ACTION$navigateFlow",
                    "callingDescriptor": "UNKNOWN",
                    "params": {
                        "request": {
                            "action": "CONTINUE_AFTER_COMMIT",
                            "serializedState": serialized_state,
                            "fields": [],
                            "uiElementVisited": True,
                            "enableTrace": False,
                        }
                    },
                }
            ]
        }
        r = self._request(28, "aura.FlowRuntimeConnect.navigateFlow", message6)

        table_value = r.json()["actions"][0]["returnValue"]["response"]["fields"][1][
            "inputs"
        ][3]["value"]

        table = json.loads(table_value)

        for row in table:
            date_str = row["col2"]
            bin_type = row["col1"]
            try:
                date_ = self._parse_date(date_str)
            except ValueError:
                _LOGGER.warning(f"date in unknown format: {date_str}")
                continue
            icon = ICON_MAP.get(bin_type.split()[-1].lower())
            entries.append(Collection(date=date_, t=bin_type, icon=icon))

        return entries
