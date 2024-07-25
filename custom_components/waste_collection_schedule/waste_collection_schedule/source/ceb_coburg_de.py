from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Coburg Entsorgungs- und Baubetrieb CEB"
DESCRIPTION = "Source for Coburg Entsorgungs- und Baubetrieb CEB."
URL = "https://www.ceb-coburg.de/"
TEST_CASES = {
    "Kanalstraße (Seite HUK)": {"street": "Kanalstraße (Seite HUK)"},
    "Plattenäcker": {"street": "Plattenäcker"},
}

ICON_MAP = {
    "Schwarz": "mdi:trash-can",
    "Grün": "mdi:package-variant",
    "Gelb": "mdi:recycle",
}


API_URL = "https://ceb-coburg.de/04_Stadtreinigung-Abfall/Abfallentsorgung-Recycling/Abfallbehaelter/muellabfuhrkalenderv2.php"
STREETS_URL = "https://ceb-coburg.de/04_Stadtreinigung-Abfall/Abfallentsorgung-Recycling/Abfallbehaelter/muellabfuhr.php"


class Source:
    def __init__(self, street: str):
        self._street: str = street

    def _get_all_supported_streets(self) -> list[str]:
        r = requests.get(STREETS_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        streets: list[str] = []
        accordion = soup.select_one("div#accordion")
        if not accordion:
            return streets

        for panel in accordion.select("div.panel-collapse"):
            for street in panel.select("a"):
                streets.append(street.get_text(strip=True))
        return streets

    def fetch(self) -> list[Collection]:
        args = {"s": self._street}

        r = requests.get(API_URL, params=args)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.select("table")

        entries = []
        for table in tables:
            for tr in table.select("tr"):
                tds = tr.select("td")
                if len(tds) != 2:
                    continue
                bin_type_tag = tds[0]
                date_tag = tds[1]
                date_string = date_tag.get_text(strip=True)
                bin_type = bin_type_tag.get_text(strip=True)

                date = datetime.strptime(date_string, "%d.%m.%Y").date()
                icon = ICON_MAP.get(bin_type)
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        if not entries:
            try:
                supported_streets = self._get_all_supported_streets()
            except Exception as e:
                raise SourceArgumentNotFound(
                    "street", self._street, f"Failed to fetch supported streets: {e}"
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "street", self._street, supported_streets
            )

        return entries
