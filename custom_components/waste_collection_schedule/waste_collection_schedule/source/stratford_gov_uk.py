import requests
from bs4 import BeautifulSoup
import dateutil.parser as date_parser
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Stratford District Council"
DESCRIPTION = "Source for Stratford District Council and their 123+ bin collection system"
URL = "https://stratford.gov.uk"

TEST_CASES = { # if you want your address removed, please submit a request and this will be done
    "Stratford DC": {"uprn": "100071513500"}, # doesnt have food waste
    "Alscot Estate": {"uprn": "10024633309"}
}

ICON_MAP = {
    "Garden waste collection": "mdi:leaf",
    "General refuse collection": "mdi:trash-can",
    "Recycling bin collection": "mdi:recycle",
    "Food waste collection": "mdi:food-apple"
}
# order of BINS is important, it's the order they appear left-to-right in the table.
BINS = [ "Food waste collection", "Recycling bin collection", "General refuse collection", "Garden waste collection" ]

API_URL = "https://www.stratford.gov.uk/waste-recycling/when-we-collect.cfm/part/calendar"
HEADERS = {
    # "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/x-www-form-urlencoded"
}

class Source:
    def __init__(self, uprn=""):
        self._payload = "frmAddress1=&frmAddress2=&frmAddress3=&frmAddress4=&frmPostcode=" # fill in the address with blanks, dont need it
        self._payload += "&frmUPRN=" + uprn # only need to provide uprn. but we DO need to have the keys for the rest of the address.

    def fetch(self):
        r = requests.post(API_URL, data = self._payload, headers=HEADERS)
        soup = BeautifulSoup(r.text, features="html.parser")

        # Retrieve collection details
        entries = []
        table = soup.find("table", class_="table") # yes really

        # each row is a date, and its given collections
        for row in table.tbody.find_all("tr"):
            # first td is the date of the collection
            date = date_parser.parse(row.find("td").text).date()

            # there are 4 bins per row, this gets them
            all_bins = row.find_all("td", class_="text-center")

            bins_collections = []

            # each bin may be "checked" to show it can be collected on that date
            for idx, cell in enumerate(all_bins):
                if cell.find("img", class_="check-img"):

                    entries.append(Collection(
                        date = date,
                        t = BINS[idx],
                        icon = ICON_MAP.get(BINS[idx])
                    ))

        return entries
