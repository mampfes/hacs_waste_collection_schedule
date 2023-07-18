from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stratford District Council"
DESCRIPTION = (
    "Source for Stratford District Council and their 123+ bin collection system"
)
URL = "https://stratford.gov.uk"

TEST_CASES = (
    {  # if you want your address removed, please submit a request and this will be done
        "Stratford DC": {"uprn": "100071513500"},  # doesn't have food waste
        "Alscot Estate": {"uprn": 10024633309},
    }
)

ICON_MAP = {
    "Garden waste": "mdi:leaf",
    "Refuse": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Food waste": "mdi:food-apple",
}
# order of BINS is important, it's the order they appear left-to-right in the table.
# these names have been chosen to accurately reflect naming convention on Stratford.gov
BINS = ["Food waste", "Recycling", "Refuse", "Garden waste"]

API_URL = (
    "https://www.stratford.gov.uk/waste-recycling/when-we-collect.cfm/part/calendar"
)
HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

DATE_FORMAT = "%A, %d/%m/%Y"  # format of the date string in the collection table


class Source:
    def __init__(self, uprn):
        # fill in the address with blanks, dont need it
        # self._payload += "&frmUPRN=" + uprn # only need to provide uprn. but we DO need to have the keys for the rest of the address.
        self._payload = {
            "frmAddress1": "",
            "frmAddress2": "",
            "frmAddress3": "",
            "frmAddress4": "",
            "frmPostcode": "",
            "frmUPRN": uprn,
        }

    def fetch(self):
        r = requests.post(API_URL, data=self._payload, headers=HEADERS)
        soup = BeautifulSoup(r.text, features="html.parser")

        # Retrieve collection details
        entries = []
        table = soup.find("table", class_="table")  # yes really

        # each row is a date, and its given collections
        for row in table.tbody.find_all("tr"):
            # first td is the date of the collection
            # format is day / month / year
            date = datetime.strptime(row.find("td").text, DATE_FORMAT).date()

            # there are 4 bins per row, this gets them
            all_bins = row.find_all("td", class_="text-center")

            # each bin may be "checked" to show it can be collected on that date
            for idx, cell in enumerate(all_bins):
                if cell.find("img", class_="check-img"):

                    entries.append(
                        Collection(date=date, t=BINS[idx], icon=ICON_MAP.get(BINS[idx]))
                    )

        return entries
