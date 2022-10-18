import json
import logging
import requests

from datetime import datetime
from waste_collection_schedule import Collection

# These two lines are needed to suppress the InsecureRequestWarning resulting from POST using verify=False
# With verify=True the POST fails due to a SSLCertVerificationError.
# using verify=False is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
import urllib3
urllib3.disable_warnings()


TITLE = "chesterfield.gov.uk"

DESCRIPTION = (
    """Source for waste collection services for Chesterfield Borough Council"""
)

URL = "https://www.chesterfield.gov.uk/"

TEST_CASES = {
    "Test_001": {"uprn": 74023685},
    "Test_002": {"uprn": "74009625"},
    "Test_003": {"uprn": "74035689"},
    "Test_004": {"uprn": "74020930"},
}


ICONS = {
    "DOMESTIC REFUSE": "mdi:trash-can",
    "DOMESTIC RECYCLING": "mdi:recycle",
    "DOMESTIC ORGANIC": "mdi:leaf",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()
        r = s.get(
            "https://www.chesterfield.gov.uk/bins-and-recycling/bin-collections/check-bin-collections.aspx"
        )

        if self._uprn:
            # POST request returns schedule for matching uprn
            payload = {
                "message": '{\"actions\":[{\"id\":\"4;a\",\"descriptor\":\"aura://ApexActionController/ACTION$execute\",\"callingDescriptor\":\"UNKNOWN\",\"params\":{\"namespace\":\"\",\"classname\":\"CBC_VE_CollectionDays\",\"method\":\"getServicesByUPRN\",\"params\":{\"propertyUprn\":\"' + self._uprn + '\",\"executedFrom\":\"Main Website\"},\"cacheable\":false,\"isContinuation\":false}}]}',
                "aura.context": '{\"mode\":\"PROD\",\"fwuid\":\"5FtqNRNwJDpZNZFKfXyAmg\",\"app\":\"c:cbc_VE_CollectionDaysLO\",\"loaded\":{\"APPLICATION@markup://c:cbc_VE_CollectionDaysLO\":\"pqeNg7kPWCbx1pO8sIjdLA\"},\"dn\":[],\"globals\":{},\"uad\":true}',
                "aura.pageURI": '/bins-and-recycling/bin-collections/check-bin-collections.aspx',
                "aura.token": 'null'
            }
            r = s.post(
                "https://myaccount.chesterfield.gov.uk/anonymous/aura?r=2&aura.ApexAction.execute=1",
                data=payload,
                verify=False,
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
                        icon=ICONS.get(waste_type.upper()),
                    )
                )

        return entries
