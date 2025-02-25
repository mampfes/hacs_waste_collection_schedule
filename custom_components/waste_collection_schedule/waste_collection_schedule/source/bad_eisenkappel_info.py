from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "Eisenkappel-Vellach"
DESCRIPTION = "Source for Eisenkappel-Vellach."
URL = "https://www.bad-eisenkappel.info/"
TEST_CASES = {"Leppen": {"region": "Leppen"}}
COUNTRY = "at"

ICON_MAP = {
    "Restmüll": "mdi:trash-can",
    "Glasbehälter": "mdi:bottle-soda",
    "Biomüll": "mdi:leaf",
    "Altpapiertonne": "mdi:package-variant",
    "Recycle": "mdi:recycle",
    "Recyclinghof": "mdi:factory",
    "Gelbe": "mdi:recycle",
}


API_URL = "https://www.bad-eisenkappel.info/gemeinde/onlineservice/abfuhrtermine.html"

PARAM_TRANSLATIONS = {
    "de": {
        "region": "Ortsteil",
    }
}


class Source:
    def __init__(self, region: str):
        self._region: str = region

    def fetch(self) -> list[Collection]:
        # get json file
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.select("table")
        entries = []
        regions = set[str]()
        for table in tables:
            trs = table.select("tr")
            for tr in trs:
                tds = tr.select("td")
                if len(tds) < 3:
                    continue
                date_str = tds[0].text.strip().split(". ")[1]

                date = datetime.strptime(date_str, "%d.%m.%y").date()
                bin_type = (
                    tds[1]
                    .text.strip()
                    .removeprefix("Abholung")
                    .removeprefix("Entleerung")
                    .strip()
                    .removeprefix("von")
                    .strip()
                    .removeprefix("der")
                    .strip()
                )
                icon = ICON_MAP.get(bin_type.split()[0].strip(", "))
                region_str = tds[2].text.strip()
                for region in region_str.split(","):
                    regions.add(region.strip())

                if (
                    region_str.lower() == "Gesamtes Gemeindegebiet".lower()
                    or self._region.lower().replace(" ", "")
                    in region_str.lower().replace(" ", "").split(",")
                ):
                    entries.append(Collection(date=date, t=bin_type, icon=icon))

        regions.remove("Gesamtes Gemeindegebiet")
        if self._region.lower().replace(" ", "") not in map(
            lambda x: x.lower().replace(" ", ""), regions
        ):
            raise SourceArgumentNotFoundWithSuggestions(
                argument="region",
                value=self._region,
                suggestions=regions,
            )

        return entries
