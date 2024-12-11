import datetime
import logging
import re

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Poznań"
DESCRIPTION = "Source for Poznań city garbage collection"
URL = "https://www.poznan.pl/mim/odpady"
TEST_CASES = {
    "Street Name": {
        "street_name": "ŚWIĘTY MARCIN",
        "street_number": "1",
    },
}

_LOGGER = logging.getLogger(__name__)


API_URL = "https://www.poznan.pl/mim/odpady/harmonogramy.html"

ICON_MAP = {
    1: "mdi:trash-can",
    2: "mdi:recycle",
    3: "mdi:recycle",
    4: "mdi:recycle",
    5: "mdi:recycle",
    6: "mdi:recycle",
    7: "mdi:trash-can",
}


class Source:
    def __init__(self, street_name: str, street_number: str | int):
        self._street_name = street_name.upper()
        self._street_number = str(street_number).upper()

    def fetch(self) -> list[Collection]:
        data = {
            "action": "search",
            "co": "waste_schedule",
            "ws_street": self._street_name,
            "ws_number": self._street_number,
        }

        r = requests.post(f"{API_URL}", data)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        year = datetime.date.today().year
        month = datetime.date.today().month

        table = soup.find("table", id="schedule_0")
        if not isinstance(table, Tag):
            raise Exception("Invalid address")

        year = datetime.date.today().year
        month = datetime.date.today().month
        formatted_date = f"{month}.{year}"

        # find all non empty tr's
        trs = [
            tr for tr in table.find_all("tr") if isinstance(tr, Tag) and tr.find_all()
        ]
        entries = []

        for row_index, row in enumerate(trs[1:]):
            all_cells = row.find_all("td")
            collection_name = all_cells[0].text.strip()
            # iterate over all rows with dates without collection name
            for cell_index, cell in enumerate(all_cells[1:]):
                if (
                    not isinstance(cell, Tag)
                    or not cell['data-value'] == formatted_date
                    or not cell.text.strip()
                ):
                    continue

                for day in cell.text.split(","):
                    day = day.strip()
                    entries.append(
                        Collection(
                            datetime.date(year, month, int(day)),
                            collection_name,
                            ICON_MAP[cell_index],
                        )
                    )

        return entries
