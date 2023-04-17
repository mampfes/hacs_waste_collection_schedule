import requests
import bs4
import re

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Basildon Council"
DESCRIPTION = "Source for basildon.gov.uk services for Basildon Council, UK."
URL = "https://basildon.gov.uk"
TEST_CASES = {
    "Test_001": {"postcode": "CM111BJ", "address": "6, HEADLEY ROAD"}
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "DryNext": "mdi:recycle",
    "GlassNext": "mdi:glass-fragile",
    "RubbishNext": "mdi:trash-can",
    "GardenAndFoodNext": "mdi:leaf",
}


class Source:
    def __init__(self, postcode, address):
        self._postcode = postcode
        self._address = address

    def fetch(self):

        s = requests.Session()

        data = {
            "__Click": "$Refresh",
            "txtPostcode": self._postcode,
            "txtAddress": self._address
        }
        schedule_request = s.post(
            f"https://www3.basildon.gov.uk/website2/postcodes.nsf/frmMyBasildon",
            headers=HEADERS,
            data=data
        )
        html_rowdata = schedule_request.content
        rowdata = bs4.BeautifulSoup(html_rowdata, "html.parser")

        # Extract bin types and next collection dates
        entries = []
        for bintype in ICON_MAP:
            for i in range(1,7):
                bintype_date = rowdata.find('input', {'name': f'{bintype}{i}'})
                if bintype_date:
                    date_str = bintype_date['value']
                    date_str = re.sub(r'\b(\d+)(st|nd|rd|th)\b', r'\1', date_str)
                    entries.append(
                        Collection(
                            t=bintype,
                            date=datetime.strptime(date_str, "%a, %d %b %Y").date(),
                            icon=ICON_MAP.get(bintype)
                        )
                    )

        return entries
