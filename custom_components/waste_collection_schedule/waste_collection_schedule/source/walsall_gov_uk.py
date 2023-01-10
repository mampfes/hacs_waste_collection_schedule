import logging
import requests

from bs4 import BeautifulSoup
from datetime import datetime

from waste_collection_schedule import Collection

TITLE = "Walsall Council"
DESCRIPTION = "Source for waste collection services from Walsall Council"
URL = "https://www.walsall.gov.uk/"
TEST_CASES = {
    "test001" : {"uprn": "100071103746"},
    "test002" : {"uprn": 100071105627},
    "test003" : {"uprn": "100071095946"},
    "test004" : {"uprn": 100071048794},    
}

API_URL = "https://cag.walsall.gov.uk"
ICON_MAP = {
    "GREY": "mdi:trash-can",
    "GREEN": "mdi:recycle",
    "BROWN": "mdi:leaf",
}
HEADERS = {
    "user-agent": "Mozilla/5.0",
}


_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, uprn=None):
        self._uprn = str(uprn)

    def fetch(self):

        s = requests.Session()

        if self._uprn:
            # GET request returns page containing links to separate collection schedules
            r = s.get(f"https://cag.walsall.gov.uk/BinCollections/GetBins?uprn={self._uprn}", headers=HEADERS)
            responseContent = r.text
            soup = BeautifulSoup(responseContent, "html.parser")
            # Extract links to collection shedule pages and iterate through the pages
            schedule_links = soup.findAll("a", {"class": "nav-link"}, href=True)
            entries = []
            for item in schedule_links:
                if "roundname" in item["href"]:
                    #get bin colour
                    bincolour = item["href"].split("=")[-1].split("%")[0].upper()
                    binURL = API_URL + item["href"]
                    r = s.get(binURL, headers=HEADERS)
                    responseContent = r.text
                    soup = BeautifulSoup(responseContent, "html.parser")
                    table = soup.findAll("td")
                    for td in table:
                        try:
                            collection_date = datetime.strptime(td.text.strip(), "%d/%m/%Y")
                            entries.append(
                                Collection(
                                    date = collection_date.date(),
                                    t = bincolour,
                                    icon = ICON_MAP.get(bincolour),
                                )
                            )
                        except ValueError:
                            pass

        return entries
