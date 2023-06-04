import json
import requests

from datetime import datetime
from time import time_ns
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

# Many thanks to dt215git for their work on the Bexley version of this provider which helped me write this.

TITLE = "Maidstone Borough Council"
DESCRIPTION = "Source for maidstone.gov.uk services for Maidstone Borough Council."
URL = "https://maidstone.gov.uk"
TEST_CASES = {
    "Test_001": {"uprn": "10022892379"}, # has mutliple collections on same week per bin type
    "Test_002": {"uprn": 10014307164}, # has duplicates of the same collection (two bins for this block of flats?)
    "Test_003": {"uprn": "200003674881"} # has garden waste collection, at time of coding
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}

# map names and icons, maidstone group food recycling for both
BIN_MAP = {
    "REFUSE": {"icon":"mdi:trash-can", "name": "Black bin and food"},
    "RECYCLING": {"icon":"mdi:recycle", "name": "Recycling bin and food"},
    "GARDEN": {"icon":"mdi:leaf", "name": "Garden bin"}
}


class Source:
    def __init__(self, uprn):
        #self._uprn = str(uprn).zfill(12)
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()

        # Set up session
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds
        session_request = s.get(
            f"https://self.maidstone.gov.uk/apibroker/domain/self.maidstone.gov.uk?_={timestamp}",
            headers=HEADERS,
        )

        # This request gets the session ID
        sid_request = s.get(
            "https://self.maidstone.gov.uk/authapi/isauthenticated?uri=https%3A%2F%2Fself.maidstone.gov.uk%2Fservice%2Fcheck_your_bin_day&hostname=self.maidstone.gov.uk&withCredentials=true",
            headers=HEADERS
        )
        sid_data = sid_request.json()
        sid = sid_data['auth-session']

        # This request retrieves the schedule
        timestamp = time_ns() // 1_000_000  # epoch time in milliseconds        
        payload = {
            "formValues": { "Your collections": {"address": {"value" : self._uprn}, "uprn": {"value": self._uprn}}}
        }

        entries = []

        # Extract bin types and next collection dates, for some reason unlike all others that use this service, you need to submit a bin type to get useful dates.
        for bin in BIN_MAP.keys():
            # set seen dates
            seen = []

            # create payload for bin type
            payload = {
                "formValues": { "Your collections": {"bin": {"value": bin}, "address": {"value" : self._uprn}, "uprn": {"value": self._uprn}}}
            }
            schedule_request = s.post(
                f"https://self.maidstone.gov.uk/apibroker/runLookup?id=5c18dbdcb12cf&repeat_against=&noRetry=false&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self&_={timestamp}&sid={sid}",
                headers=HEADERS,
                json=payload
            )
            rowdata = json.loads(schedule_request.content)['integration']['transformed']['rows_data']
            for item in rowdata:
                collectionDate = rowdata[item]["Date"]
                # need to dedupe as MBC seem to list the same collection twice for some places
                if collectionDate not in seen:
                    entries.append(
                        Collection(
                            t=BIN_MAP[bin]['name'],
                            date=datetime.strptime(
                                collectionDate, "%d/%m/%Y"
                            ).date(),
                            icon=BIN_MAP.get(bin).get('icon'),
                        )
                    )
                    # add this date to seen so we don't use it again
                    seen.append(collectionDate)

        return entries