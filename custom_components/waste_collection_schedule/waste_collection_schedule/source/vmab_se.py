import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentRequiredWithSuggestions

TITLE = "Västblekinge Miljö AB"
DESCRIPTION = "Source for Västblekinge Miljö AB."
URL = "https://vmab.se/"

TEST_CASES = {
    "Kvarnvägen 1": {"address": "Kvarnvägen 1 Laxens Hus", "pickup_id": "801602949"},
}

ICON_MAP = {
    "Färgat glas": "mdi:glass-pint",
    "Ofärgat glas": "mdi:glass-pint-outline",
    "Plastförp": "mdi:recycle",
    "Matavfall": "mdi:food",
    "Pappersförp": "mdi:package-variant",
    "Restavfall": "mdi:trash-can",
    "Wellpapp": "mdi:layers-triple",
    "Metallförp": "mdi:wrench",
}

SEARCH_URL = "https://cal.vmab.se/search_suggestions.php"
API_URL = "https://cal.vmab.se/get_data.php"

HEADERS = {"User-Agent": "Mozilla/5.0"}


class Source:
    def __init__(self, address: str, pickup_id: str):
        self._address: str = address
        self._pickup_id: str = pickup_id

    def fetch(self) -> list[Collection]:
        if not self._pickup_id:
            self._pickup_id_suggestions()

        data = {
            "chosen_address": self._address,
            "chosen_address_pickupid": self._pickup_id,
        }
        r = requests.post(API_URL, data=data, headers=HEADERS)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        javascript = soup.find("script").string
        javascript = javascript.split("events: ", 1)[-1].rsplit(",\r\n/*", 1)[0] + "]"
        javascript = javascript.replace("'", '"')
        javascript = javascript.replace("title:", '"title":')
        javascript = javascript.replace("start:", '"start":')

        schedule = json.loads(javascript)

        if not schedule:
            raise Exception("No schedule found")

        entries = []
        for c in schedule:
            date_ = datetime.strptime(c["start"], "%Y-%m-%d").date()

            bin_type = c["title"].split(",")[0]
            icon = ICON_MAP.get(bin_type)

            entries.append(Collection(date_, c["title"], icon))

        return entries

    """ helper that returns available pickup ids for address """

    def _pickup_id_suggestions(self):
        data = {"search_address": self._address}
        r = requests.post(SEARCH_URL, data=data, headers=HEADERS)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        addresses = soup.find_all("li")
        if not addresses:
            raise Exception("No addresses found")

        options = []
        for a in addresses:
            options.append("{} ({})".format(a["id"], a.text))

        raise SourceArgumentRequiredWithSuggestions(
            "pickup_id", self._pickup_id, options
        )
