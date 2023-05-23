import requests
import bs4
import re

from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Barnsley Council"
DESCRIPTION = "Source for barnsley.gov.uk services for Barnsley MBC, UK."
URL = "https://wwwapplications.barnsley.gov.uk/wastemvc/ViewCollection/SelectAddress"
TEST_CASES = {
    "Test_001": {"postcode": "S703QN", "address": "18"}
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}
ICON_MAP = {
    "BLUE": "mdi:recycle",
    "BROWN": "mdi:glass-fragile",
    "GREY": "mdi:trash-can",
    "GREEN": "mdi:leaf",
}


class Source:
    def __init__(self, postcode, houseNo):
        self._postcode = postcode
        self._houseNo = houseNo

    def fetch(self):

        s = requests.Session()

        data = {
            "person1_FindAddress": "Find address",
            "personInfo.person1.HouseNumberOrName": self._houseNo,
            "personInfo.person1.Postcode": self._postcode
        }
        schedule_request = s.post(
            f"https://wwwapplications.barnsley.gov.uk/wastemvc/ViewCollection/SelectAddress",
            headers=HEADERS,
            data=data
        )
        html_rowdata = schedule_request.content
        soup = bs4.BeautifulSoup(html_rowdata, "html.parser")
        entries = []

        nextDate = soup.find_all("em", {"class": "ui-bin-next-date"})[0].text
        if nextDate == "Today":
            nextDate = datetime.today().date()
        else:
            nextDate = datetime.strptime(nextDate, "%A, %B %d, %Y").date()
        nextBins = soup.find_all("p", {"class": "ui-bin-next-type"})[0].text.strip().split(", ")
        for binType in nextBins:
            collection_type = binType.strip()
            entries.append(
                Collection(
                    date = nextDate,
                    t = collection_type,
                    icon = ICON_MAP.get(collection_type.upper())
                )
            )
                
        # Extract bin types and next collection dates
        for collection in soup.findAll('tbody')[0].findAll('tr'):
            try:
                # Getting Date
                line = collection.findAll('td')
                date_str = line[0].text.strip()
                collection_date = datetime.strptime(date_str, "%A, %B %d, %Y").date()
                # Getting the collection type
                bins = line[1].text.strip().split(", ")
                for binType in bins:
                    collection_type = binType.strip()

                    # Append to entries for main program
                    entries.append(
                        Collection(
                            date = collection_date,
                            t = collection_type,
                            icon = ICON_MAP.get(collection_type.upper())
                        )
                    )
            except ValueError:
                pass

        return entries
