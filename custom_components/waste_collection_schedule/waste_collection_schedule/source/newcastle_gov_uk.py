import logging
import re
from datetime import datetime
import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# These lines are needed to suppress the InsecureRequestWarning resulting from the POST verify=False option
# With verify=True the POST fails due to a SSLCertVerificationError.
# The following links may provide a better way of dealing with this, as using verify=False is not ideal:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
import urllib3
urllib3.disable_warnings()

_LOGGER = logging.getLogger(__name__)

TITLE = "Newcastle City Council"
DESCRIPTION = "Source for waste collection services for Newcastle City Council"
URL = "https://community.newcastle.gov.uk"
TEST_CASES = {"Test_001": {"uprn": "004510053797"}, "Test_002": {"uprn": 4510053797}}


API_URL = "https://community.newcastle.gov.uk/my-neighbourhood/ajax/getBinsNew.php"
REGEX = (
    "<strong>(Green|Blue|Brown) [bB]in \\((Domestic|Recycling|Garden)( Waste)?\\) details: <\\/strong><br\\/>"
    "collection day : [a-zA-Z]*day<br\\/>"
    "Next collection : ([0-9]{2}-[A-Za-z]+-[0-9]{4})"
)
ICON_MAP = {
    "DOMESTIC": "mdi:trash-can",
    "RECYCLING": "mdi:recycle",
    "GARDEN": "mdi:leaf",
}


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn).zfill(12)
        self._session = requests.Session()

    def fetch(self):
        entries = []
        res = requests.get(f"{URL}?uprn={self._uprn}")
        collections = re.findall(REGEX, res.text)

        for collection in collections:
            collection_type = collection[1]
            collection_date = collection[3]
            entries.append(
                Collection(
                    date=datetime.strptime(collection_date, "%d-%b-%Y").date(),
                    t=collection_type,
                    icon=ICON_MAP.get(collection_type.upper()),
                )
            )

        return entries
