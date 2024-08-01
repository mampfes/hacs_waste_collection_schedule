from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Reno Djurs"
DESCRIPTION = "Reno Djurs collections for Djursland"
URL = "https://renodjurs.dk"
TEST_CASES = {
    "TestCase1": {
        "id": "46000",
    },
    "TestCase2": {
        "id": "45000",
    },
    "TestCase3": {
        "id": 44000,
    },
}

ICON_MAP = {
    "REST-MAD": "mdi:trash-can",
    "PAP-PAPIR": "mdi:newspaper",
    "PLAST-GLAS-METAL": "mdi:bottle-wine",
}


class Source:
    def __init__(self, id: str | int):
        self._id = str(id)
        self._api_url = f"https://minside.renodjurs.dk/Ordninger.aspx?id={self._id}"

    def fetch(self):
        session = requests.Session()

        entries = []

        r = session.get(self._api_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        container = soup.find("table", {"class": "table"})
        rows = container.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) <= 4:
                continue

            raw_type = cells[1].get_text()
            fraktion = "unknown"
            icon = None
            current_pickup = None
            next_pickup = None

            if "rest" in raw_type and "mad" in raw_type:
                fraktion = "Rest- og Madaffald"
                icon = ICON_MAP.get("REST-MAD")
            elif "plast" in raw_type and "glas" in raw_type:
                fraktion = "Plast-, Glas- og Metalaffald"
                icon = ICON_MAP.get("PLAST-GLAS-METAL")
            elif "papir" in raw_type:
                fraktion = "Pap- og Papiraffald"
                icon = ICON_MAP.get("PAP-PAPIR")

            if cells[3].get_text() is None or cells[3].get_text() == "":
                continue

            current_pickup = datetime.strptime(cells[3].get_text(), "%d-%m-%Y").date()
            next_pickup = datetime.strptime(cells[4].get_text(), "%d-%m-%Y").date()

            if current_pickup == datetime.now().date():
                entries.append(
                    Collection(
                        date=current_pickup,
                        t=fraktion,
                        icon=icon,
                    )
                )

            entries.append(
                Collection(
                    date=next_pickup,
                    t=fraktion,
                    icon=icon,
                )
            )

        return entries
