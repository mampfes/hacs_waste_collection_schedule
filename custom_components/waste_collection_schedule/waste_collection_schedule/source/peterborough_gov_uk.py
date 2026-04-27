import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ICS import ICS

TITLE = "Peterborough City Council"
DESCRIPTION = "Source for peterborough.gov.uk services for Peterborough"
URL = "https://peterborough.gov.uk"
TEST_CASES = {
    "houseUprn": {"postcode": "PE57AX", "uprn": "100090214774"},
}

API_URLS = {
    "collection": "https://report.peterborough.gov.uk/waste/{postcode}:{uprn}/calendar.ics",
}

ICON_MAP = {
    "Empty Bin 240L Black": "mdi:trash-can",
    "Empty Bin 240L Green": "mdi:recycle",
    "Empty Bin 240L Brown": "mdi:leaf",
}


class Source:
    def __init__(self, postcode, uprn):
        self._post_code = postcode
        self._uprn = uprn
        self._ics = ICS()

    def fetch(self):
        if not self._post_code:
            raise SourceArgumentNotFound("postcode", "Postcode is required")

        if not self._uprn:
            raise SourceArgumentNotFound("uprn", "UPRN is required")

        ics_url = API_URLS["collection"].format(
            postcode=self._post_code, uprn=self._uprn
        )
        r = requests.get(ics_url, timeout=10)
        r.raise_for_status()

        dates = self._ics.convert(r.text)

        entries = []
        for item in dates:
            bin_type = item[1]
            entries.append(
                Collection(
                    date=item[0],
                    t=bin_type,
                    icon=ICON_MAP.get(bin_type),
                )
            )

        return entries
