from datetime import datetime

from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.SSLError import get_legacy_session

TITLE = "Blackburn with Darwen Borough Council"
DESCRIPTION = "Source for mybins.blackburn.gov.uk services for Blackburn with Darwen Borough Council, UK."
URL = "https://blackburn.gov.uk/"
TEST_CASES = {
    "Test_001": {"uprn": "10091617919"},
    "Test_002": {"uprn": "100010732130"},
    "Test_003": {"uprn": 100010729702},
    "Test_004": {"uprn": 100010751876},
}

ICON_MAP = {
    "Burgundy": "mdi:trash-can",
    "Grey": "mdi:recycle",
    "Blue": "mdi:package-variant",
}

API_URL = "https://mybins.blackburn.gov.uk/api/mybins/getbincollectiondays"


# With verify=True the POST fails due to a SSLCertVerificationError.
# Using verify=False works, but is not ideal. The following links may provide a better way of dealing with this:
# https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings
# https://urllib3.readthedocs.io/en/1.26.x/user-guide.html#ssl
# These two lines areused to suppress the InsecureRequestWarning when using verify=False
import urllib3

urllib3.disable_warnings()


class Source:
    def __init__(self, uprn):
        self._uprn = str(uprn)

    def fetch(self):
        date = datetime.now()

        # that's not very nice, but it is the only way I got it to work
        s = get_legacy_session()
        s.get_adapter("https://").ssl_context.check_hostname = False

        year = date.year
        month = date.month
        entries = []
        for i in range(1, 13):
            PARAMS = {
                "month": month,
                "year": year,
                "uprn": self._uprn,
            }

            r = s.get(
                API_URL,
                params=PARAMS,
                verify=False,
            )
            r.raise_for_status()

            collection_days = r.json()["BinCollectionDays"]

            for collection_day in collection_days:
                if collection_day is not None and isinstance(collection_day, list):
                    for collection in collection_day:
                        entries.append(
                            Collection(
                                date=datetime.fromisoformat(
                                    collection["CollectionDate"]
                                ).date(),
                                t=collection["BinType"],
                                icon=ICON_MAP.get(collection["BinType"].split(" ")[0]),
                            )
                        )

            month += 1
            if month > 12:
                month = 1
                year += 1

        return entries
