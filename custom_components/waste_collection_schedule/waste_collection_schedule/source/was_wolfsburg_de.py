from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Wolfsburger Abfallwirtschaft und Straßenreinigung"
DESCRIPTION = "Source for waste collections for WAS-Wolfsburg, Germany."
URL = "https://was-wolfsburg.de"
TEST_CASES = {
    "Barnstorf": {"city": "Barnstorf", "street": "Bahnhofspassage"},
    "Sülfeld": {"city": "Sülfeld", "street": "Bärheide"},
}

ICON_MAP = {
    "Gelber Sack": "mdi:recycle",
    "Bioabfall": "mdi:leaf",
    "Restabfall": "mdi:trash-can",
    "Altpapier": "mdi:file-document-outline",
}


class Source:
    def __init__(self, street: str | None, city: str | None):
        self._street = street
        self._city = city
        if street is None and city is None:
            raise ValueError("Either street or city must be set")

    def get_date(self, tag: Tag, gelber_sack: bool) -> date | None:
        if gelber_sack:
            date_tag = tag.select_one("div.single-termin-date")
            if not date_tag:
                return None
            date_string = "".join(
                [t for t in date_tag.contents if isinstance(t, str)]
            ).strip()
        else:
            date_tag = tag.select_one("div.single-termin-day")
            if not date_tag:
                return None
            # remove all inner tags
            date_string = (
                "".join([t for t in date_tag.contents if isinstance(t, str)])
                .split(",")[1]
                .strip()
            )

        return datetime.strptime(date_string, "%d.%m.%Y").date()

    def get_data(
        self, soup: BeautifulSoup, gelber_sack: bool = False
    ) -> list[Collection]:
        entries = []
        for entry in soup.select("div.single-termin"):
            d = self.get_date(entry, gelber_sack)
            if not gelber_sack:
                bin_type_tag = entry.select_one("div.single-termin-abfall")
                if not bin_type_tag or not d:
                    continue
                bin_type = bin_type_tag.text.strip()
            else:
                bin_type = "Gelber Sack"

            entries.append(Collection(date=d, t=bin_type, icon=ICON_MAP.get(bin_type)))
        return entries

    def fetch(self) -> list[Collection]:
        entries = []
        if self._street is not None:
            data = {"loc": self._street}
            r = requests.post(
                "https://was-wolfsburg.de/wp-content/themes/astra-child/search_restabfall/search.php",
                data=data,
            )
            answer = r.json()
            soup = BeautifulSoup(answer["string"], "html.parser")
            entries += self.get_data(soup)
        if self._city is not None:
            data = {"loc": self._city}
            r = requests.post(
                "https://was-wolfsburg.de/wp-content/themes/astra-child/search_gelbersack/search.php",
                data=data,
            )
            answer = r.json()
            soup = BeautifulSoup(answer["string"], "html.parser")
            entries += self.get_data(soup, True)

        return entries
