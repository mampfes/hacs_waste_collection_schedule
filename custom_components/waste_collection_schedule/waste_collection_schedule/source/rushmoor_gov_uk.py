import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "rushmoor.gov.uk"
DESCRIPTION = "Source for rushmoor.gov.uk services for Rushmoor, UK."
# Find the UPRN of your address using https://www.findmyaddress.co.uk/search
URL = "https://rushmoor.gov.uk"
TEST_CASES = {
    "GU14": {"uprn": "100060551749"},
}

ICON_MAP = {
    "Refuse bin": "mdi:trash-can",
    "Recycle bin": "mdi:recycle",
}

API_URL = "https://www.rushmoor.gov.uk/recycling-rubbish-and-environment/bins-and-recycling/download-or-print-your-bin-collection-calendar/"


class Source:
    def __init__(self, uprn):
        self._uprn = uprn
        self._ics = ICS()

    def fetch(self):
        params = {"uprn": self._uprn, "weeks": "16"}
        r = requests.post(API_URL, params=params)
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for d in dates:
            for wasteType in d[1].split("&"):
                wasteType = wasteType.strip()
                entries.append(
                    Collection(
                        d[0],
                        wasteType,
                        icon=ICON_MAP[wasteType],
                    )
                )
        return entries
