import logging
import time
from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Cheshire West and Chester Council"
DESCRIPTION = (
    "Source for waste collection services for Cheshire West and Chester Council"
)
URL = "https://www.cheshirewestandchester.gov.uk"

TEST_CASES = {
    "Chester": {"uprn": 100010030086},
    "Chester - string": {"uprn": "100010030086"},
    "Northwich": {"uprn": 10011715183},
    "Hartford": {"uprn": 100010181592},
    "Tarporley": {"uprn": 10014514851},
    "Knutsford - no results": {
        "uprn": 100010132172
    },  # Knutsford is in Cheshire East and shouldn't have any collection information!
}

ICON_MAP = {
    "Domestic": "mdi:trash-can",
    "Food": "mdi:food-apple",
    "Recycling": "mdi:recycle",
    "Garden": "mdi:leaf",
}

API_URLS = {
    "session": "https://my.cheshirewestandchester.gov.uk/en/AchieveForms/?form_uri=sandbox-publish://AF-Process-0187a2f6-15cb-413a-8a3f-b6d14d63da57/AF-Stage-e18b38ff-be8a-45f4-ac14-f8821024f0c4/definition.json&redirectlink=%2Fen&cancelRedirectLink=%2Fen&consentMessage=yes",
    "auth": "https://my.cheshirewestandchester.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fmy.cheshirewestandchester.gov.uk%2Fen%2FAchieveForms%2F%3Fform_uri%3Dsandbox-publish%3A%2F%2FAF-Process-0187a2f6-15cb-413a-8a3f-b6d14d63da57%2FAF-Stage-e18b38ff-be8a-45f4-ac14-f8821024f0c4%2Fdefinition.json%26redirectlink%3D%2Fen%26cancelRedirectLink%3D%2Fen%26consentMessage%3Dyes&hostname=my.cheshirewestandchester.gov.uk&withCredentials=true",
    "authResp": "https://my.cheshirewestandchester.gov.uk/apibroker/runLookup?id=609b918c7dd6d&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
    "serviceTypes": "https://my.cheshirewestandchester.gov.uk/apibroker/runLookup?id=6101d1a29ba09&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
    "schedule": "https://my.cheshirewestandchester.gov.uk/apibroker/runLookup?id=6101d23110243&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AchieveForms",
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
