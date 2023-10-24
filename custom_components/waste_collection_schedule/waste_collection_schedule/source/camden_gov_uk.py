import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "London Borough of Camden"
DESCRIPTION = "Source for London Borough of Camden."
URL = "https://www.camden.gov.uk/"
TEST_CASES = {
    "Cannon Place": {"uprn": "5061647"},
    "Red Lion Street": {"uprn": 5121151},
}


ICON_MAP = {
    "rubbish": "mdi:trash-can",
    "garden waste": "mdi:leaf",
    "food": "mdi:food",
    "recycling": "mdi:recycle",
}


API_URL = "https://environmentservices.camden.gov.uk/property/{uprn}"
ICS_URL = "https://environmentservices.camden.gov.uk{href}"


class Source:
    def __init__(self, uprn: str | int):
        self._uprn: str = str(uprn)
        self._ics = ICS()

    def fetch(self):

        # get collection overview page
        r = requests.get(API_URL.format(uprn=self._uprn))
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # get all ICS links (Add to my calendar)
        ics_urls = []
        for a in soup.find_all("a"):
            if a["href"].startswith("/ical/"):
                ics_urls.append(ICS_URL.format(href=a["href"]))

        # get all collections from ICS files
        collections = []
        for ics_url in ics_urls:
            r = requests.get(ics_url)
            r.raise_for_status()
            collections.extend(self._ics.convert(r.text))

        entries = []
        for d in collections:
            bin_type = d[1].replace("Reminder", "").replace(" - ", "").strip()
            icon = ICON_MAP.get(
                bin_type.lower()
                .replace("domestic", "")
                .replace("collection", "")
                .strip()
            )
            entries.append(Collection(date=d[0], t=bin_type, icon=icon))

        return entries
