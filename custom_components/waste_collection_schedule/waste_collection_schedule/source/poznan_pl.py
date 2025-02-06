import datetime
import logging

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
    "Odpady zmieszane": "mdi:trash-can",
    "Papier": "mdi:newspaper-variant-outline",
    "Metale i tworzywa sztuczne": "mdi:bottle-soda-classic-outline",
    "Szkło": "mdi:glass-fragile",
    "Bioodpady": "mdi:recycle",
    "Odpady wystawkowe": "mdi:cupboard",
    "Drzewka świąteczne": "mdi:pine-tree",
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

        # Find all dates with available scheduling
        date_selector_wrapper = soup.find("div", id="month_selector_0_wrapper")
        if not isinstance(date_selector_wrapper, Tag):
            raise Exception("Could not parse page with waste scheduling")

        date_rows = date_selector_wrapper.find_all("div", {"class": "select_element"})
        formatted_dates = [
            date['value'] for date in date_rows if isinstance(date, Tag)
        ]

        table = soup.find("table", id="schedule_0")
        if not isinstance(table, Tag):
            raise Exception("Invalid address")

        entries = []
        for formatted_date in formatted_dates:
            date = datetime.datetime.strptime(formatted_date, '%m.%Y').date()
            year = date.year
            month = date.month

            # find all non empty tr's
            trs = [
                tr for tr in table.find_all("tr") if isinstance(tr, Tag) and tr.find_all()
            ]

            for row in trs[1:]:  # Skipping first row since it is a header
                all_cells = row.find_all("td")
                collection_name = all_cells[0].text.strip()
                # iterate over all rows with dates without collection name
                for cell in all_cells[1:]:
                    if (
                        not isinstance(cell, Tag)
                        or not cell["data-value"] == formatted_date
                        or not cell.text.strip()
                    ):
                        continue

                    for day in cell.text.split(","):
                        day = day.strip()
                        entries.append(
                            Collection(
                                datetime.date(year, month, int(day)),
                                collection_name,
                                ICON_MAP.get(collection_name, "mdi:recycle"),
                            )
                        )

        return entries
