import json
import logging
import requests

from datetime import datetime
from waste_collection_schedule import Collection

# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# These two lines areused to suppress the InsecureRequestWarning when using verify=False
import urllib3
urllib3.disable_warnings()


TITLE = "Chesterfield Borough Council"
DESCRIPTION = "Source for waste collection services for Chesterfield Borough Council"
URL = "https://www.chesterfield.gov.uk/"

HEADERS = {
    "user-agent": "Mozilla/5.0",
}

TEST_CASES = {
    "Test_001": {"uprn": 74023685},
    "Test_002": {"uprn": "74009625"},
    "Test_003": {"uprn": "74035689"},
    "Test_004": {"uprn": "74020930"},
}

ICON_MAP = {
    "DOMESTIC REFUSE": "mdi:trash-can",
    "DOMESTIC RECYCLING": "mdi:recycle",
    "DOMESTIC ORGANIC": "mdi:leaf",
}

API_URLS = {
    "session": "https://www.chesterfield.gov.uk/bins-and-recycling/bin-collections/check-bin-collections.aspx",
    "fwuid": "https://myaccount.chesterfield.gov.uk/anonymous/c/cbc_VE_CollectionDaysLO.app?aura.format=JSON&aura.formatAdapter=LIGHTNING_OUT",
    "search": "https://myaccount.chesterfield.gov.uk/anonymous/aura?r=2&aura.ApexAction.execute=1",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()
        r = s.get(
            API_URLS["session"],
            headers=HEADERS,
        )

        # Capture fwuid value
        r = s.get(
            API_URLS["fwuid"],
            verify=False,
            headers=HEADERS,
        )
        resp = json.loads(r.content)
        fwuid = resp["auraConfig"]["context"]["fwuid"]

        if self._uprn:
            # POST request returns schedule for matching uprn
            payload = {
                "message": '{"actions":[{"id":"4;a","descriptor":"aura://ApexActionController/ACTION$execute","callingDescriptor":"UNKNOWN","params":{"namespace":"","classname":"CBC_VE_CollectionDays","method":"getServicesByUPRN","params":{"propertyUprn":"'
                + self._uprn
                + '","executedFrom":"Main Website"},"cacheable":false,"isContinuation":false}}]}',
                "aura.context": '{"mode":"PROD","fwuid":"'
                + fwuid
                + '","app":"c:cbc_VE_CollectionDaysLO","loaded":{"APPLICATION@markup://c:cbc_VE_CollectionDaysLO":"pqeNg7kPWCbx1pO8sIjdLA"},"dn":[],"globals":{},"uad":true}',
                "aura.pageURI": "/bins-and-recycling/bin-collections/check-bin-collections.aspx",
                "aura.token": "null",
            }
            r = s.post(
                API_URLS["search"],
                data=payload,
                verify=False,
                headers=HEADERS,
            )
            data = json.loads(r.content)

        entries = []

        # Extract waste types and dates from json
        for item in data["actions"][0]["returnValue"]["returnValue"]["serviceUnits"]:
            try:
                waste_type = item["serviceTasks"][0]["taskTypeName"]
            except IndexError:
                # Commercial collection schedule for Residential properties is empty generating IndexError
                pass
            else:
                waste_type = str(waste_type).replace("Collect ", "")
                dt_zulu = item["serviceTasks"][0]["serviceTaskSchedules"][0]["nextInstance"]["currentScheduledDate"]
                dt_utc = datetime.strptime(dt_zulu, "%Y-%m-%dT%H:%M:%S.%f%z")
                dt_local = dt_utc.astimezone(None)
                entries.append(
                    Collection(
                        date=dt_local.date(),
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type.upper()),
                    )
                )

        return entries
