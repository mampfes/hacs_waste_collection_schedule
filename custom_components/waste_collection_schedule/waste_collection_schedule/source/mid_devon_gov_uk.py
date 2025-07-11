import logging
import time
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Mid Devon District Council"
DESCRIPTION = (
    "Source for waste collection services for Mid Devon District Council"
)
URL = "https://www.middevon.gov.uk"

TEST_CASES = {
    "Cullompton": {"uprn": 100040354099},
    "Cullompton - string": {"uprn": "100040354099"},  # Knutsford is in Cheshire East and shouldn't have any collection information!
}

ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Food": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}

API_URLS = {
    "session": "https://my.middevon.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-2289dd06-9a12-4202-ba09-857fe756f6bd/AF-Stage-eb382015-001c-415d-beda-84f796dbb167/definition.json&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes",
    "auth": "https://my.middevon.gov.uk/authapi/isauthenticated?uri=https%253A%252F%252Fmy.middevon.gov.uk%252Fen%252FAchieveForms%252F%253Fform_uri%253Dsandbox-publish%253A%252F%252FAF-Process-927a4f8b-67a7-4c41-8e39-00479c300a63%252FAF-Stage-eb382015-001c-415d-beda-84f796dbb167%252Fdefinition.json%2526redirectlink%253D%25252Fen%2526cancelRedirectLink%253D%25252Fen%2526consentMessage%253Dyes&hostname=my.middevon.gov.uk&withCredentials=true",
    "authResp": "https://my.middevon.gov.uk/apibroker/runLookup?id=645e14020c9cc&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
    "serviceTypes": "https://my.middevon.gov.uk/apibroker/runLookup?id=645e14020c9cc&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
    "schedule": "https://my.middevon.gov.uk/apibroker/runLookup?id=645e14020c9cc&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
}

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn: str):
        self._uprn = str(uprn)

    def fetch(self):
        s = requests.Session()

        # Get session cookies
        r0 = s.get(API_URLS["session"], headers=HEADERS)
        r0.raise_for_status()

        # Get session key from the PHPSESSID (in the cookies)
        authRequest = s.get(API_URLS["auth"], headers=HEADERS)
        authData = authRequest.json()
        sessionKey = authData["auth-session"]

        now = time.time_ns() // 1_000_000
        urlNonce = str(now)

        # Get AuthenticateResponse nonce
        authRespRequest = s.post(
            API_URLS["authResp"] + "&_" + urlNonce + "&sid=" + sessionKey,
            headers=HEADERS,
        )
        authenticateResponseNonce = self.achieveFormsData(authRespRequest)["0"][
            "AuthenticateResponse"
        ]

        # This payload is used for all subsequent requests
        uprnPayload = {
            "formValues": {
                "Section 1": {
                    "AuthenticateResponse": {
                        "name": "AuthenticateResponse",
                        "value": authenticateResponseNonce,
                    },
                    "UPRN": {"name": "UPRN", "value": self._uprn},
                }
            }
        }

        # Query service types with UPRN and map to generic service name
        #
        # Not all serviced UPRNs within the area share the same service type names!
        # so we need to map them back to a generic service for the icon map...
        #
        # E.g. In Chester:
        #  - Empty Black Sacks -> Domestic
        #  - Empty Recycling   -> Recycling
        #  - Empty 23L Caddy   -> Food
        #  - Empty 240L Garden -> Garden
        #
        # and in a different area of Cheshire West, it could be:
        #  - Empty 180l Domestic -> Domestic
        #  - Empty 180L Blue     -> Recycling
        #  - Empty 180L Red      -> Recycling
        #  - Empty 23L Caddy     -> Food
        #  - Empty 240L Garden   -> Garden
        scheduleRequest = s.post(
            API_URLS["serviceTypes"] + "&_" + urlNonce + "&sid=" + sessionKey,
            headers=HEADERS,
            json=uprnPayload,
        )
        data = self.achieveFormsData(scheduleRequest)

        if len(data) < 1:
            _LOGGER.warn("couldn't find service data for UPRN %s", self._uprn)
            return []

        # Map non-generic service type names to generic service type
        serviceTypeToGenericService = {}
        for service in data.values():
            genericService = service["service"].strip()
            if ICON_MAP.get(genericService) is not None:
                serviceTypeToGenericService[service["serviceType"]] = genericService

        # Now query the jobs (collection schedule)
        scheduleRequest = s.post(
            API_URLS["schedule"] + "&_" + urlNonce + "&sid=" + sessionKey,
            headers=HEADERS,
            json=uprnPayload,
        )
        data = self.achieveFormsData(scheduleRequest)

        if len(data) < 1:
            _LOGGER.warn("couldn't find collection data for UPRN %s", self._uprn)
            return []

        entries = []

        for collection in data.values():
            date = datetime.strptime(
                collection["collectionDateTime"], "%Y-%m-%dT%H:%M:%S"
            ).date()
            collection_type = collection["serviceType"]
            # Only emit the collection if it's a recognised collection type (I.e. Ignore: "BULKY BOOKINGS" and whatever else crops up)
            if serviceTypeToGenericService.get(collection_type) is not None:
                collection_type_generic = serviceTypeToGenericService[collection_type]
                entries.append(
                    Collection(
                        date=date,
                        t=collection_type,
                        icon=ICON_MAP.get(collection_type_generic),
                    )
                )
            else:
                _LOGGER.debug("unknown collection_type %s", collection_type)

        return entries

    # unwraps data from an AchieveForms response
    def achieveFormsData(self, data):
        return data.json()["integration"]["transformed"]["rows_data"]
