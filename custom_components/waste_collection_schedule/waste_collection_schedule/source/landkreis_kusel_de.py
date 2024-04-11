from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup, NavigableString
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Kusel"
DESCRIPTION = "Source for Landkreis Kusel."
URL = "https://www.landkreis-kusel.de/"
TEST_CASES = {
    "Adenbach": {"ortsgemeinde": "Adenbach"},
    "St. Julian - Eschenau": {"ortsgemeinde": "St. Julian - Eschenau"},
    "rutsweiler glan (wrong spelling)": {"ortsgemeinde": "rutsweiler glan"},
}


ICON_MAP = {
    "restmüll": "mdi:trash-can",
    "glasabfuhr": "mdi:bottle-soda",
    "bioabfall": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "wertstoffsäcke": "mdi:recycle",
    "umweltmobil": "mdi:dump-truck",
}


API_URL = "https://abfallwirtschaft.landkreis-kusel.de"


def make_comparable(ortsgemeinde: str) -> str:
    return (
        ortsgemeinde.lower()
        .replace("-", "")
        .replace(".", "")
        .replace("/", "")
        .replace(" ", "")
    )


class Source:
    def __init__(self, ortsgemeinde: str):
        self._ortsgemeinde: str = make_comparable(ortsgemeinde)
        self._ics = ICS()

    def fetch(self):
        entries = self.get_data(API_URL)
        try:
            if (
                sorted(entries, key=lambda x: x.date)[0].date.year
                != datetime.now().year
            ):
                entries += self.get_data(
                    API_URL.replace(
                        "abfallwirtschaft", f"abfall{str(datetime.now().year)[2:]}"
                    )
                )
        except Exception:
            pass
        return entries

    def get_data(self, api_url):
        s = requests.Session()
        # get json file
        r = s.get(api_url)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        select = soup.find("select", {"id": "search_ak_pickup_akPickup"})

        if not select or isinstance(select, NavigableString):
            raise Exception("Invalid response from API")

        pickup_id = None
        for option in select.find_all("option"):
            if make_comparable(option.text) == self._ortsgemeinde:
                pickup_id = option["value"]
                break

        if not pickup_id:
            raise Exception(
                f"could not find matching 'Ortsgemeinde' please check your spelling at {api_url}"
            )
        now = datetime.now()
        args = {
            "search_ak_pickup[akPickup]": pickup_id,
            "search_ak_pickup[wasteType]": "0",
            "search_ak_pickup[startDate]": now.strftime("%Y-%m-%d"),
            "search_ak_pickup[endDate]": (now + timedelta(days=365)).strftime(
                "%Y-%m-%d"
            ),
            "search_ak_pickup[search]": "",
        }

        r = s.post(api_url, data=args)
        r.raise_for_status()

        r = s.get(f"{api_url}/ical")
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].lower())))

        return entries
