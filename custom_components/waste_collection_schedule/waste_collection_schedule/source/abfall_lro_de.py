from datetime import datetime
from typing import Literal

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.ICS import ICS

TITLE = "Landkreis Rostock"
DESCRIPTION = "Source for Landkreis Rostock."
URL = "https://www.abfall-lro.de/"
TEST_CASES = {
    "Alt Kätwin": {
        "municipality": "Alt Kätwin",
        "black_rhythm": "2w",
        "green_rhythm": "4w",
    },
    "Altenhagen (Lohmen)": {
        "municipality": "Altenhagen (Lohmen)",
        "black_rhythm": "2w",
        "green_rhythm": "2w",
    },
    "Qualitz": {
        "municipality": "Qualitz",
        "black_rhythm": "",
        "green_rhythm": "2w",
        "green_seasonal": True,
    },
}


ICON_MAP = {
    "Schwarze": "mdi:trash-can",
    "Grüne": "mdi:leaf",
    "Blaue": "mdi:package-variant",
    "Gelbe": "mdi:recycle",
}


API_URL = "https://www.abfall-lro.de/de/abfuhrtermine/"
ICAL_URL = "https://www.abfall-lro.de/default-wGlobal/wGlobal/abfuhrtermine/ical.php"

RHYTHMS = Literal["2w", "4w", ""]

PARAM_TRANSLATIONS = {
    "de": {
        "municipality": "Gemeinde",
        "black_rhythm": "Schwarze Tonne Rythmus",
        "green_rhythm": "Gelbe Tonne Rythmus",
        "black_seasonal": "Schwarze Tonne Saisonal",
        "green_seasonal": "Gelbe Tonne Saisonal",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "municipality": "Name of the municipality, should match the name shown https://www.abfall-lro.de/de/abfuhrtermine/ (including sub region in bracktes)",
        "black_rhythm": "Rhythm of the black bin collection",
        "green_rhythm": "Rhythm of the green bin collection",
        "black_seasonal": "Check if the black bins are only collected seasonally",
        "green_seasonal": "Check if the green bins are only collected seasonally",
    },
    "de": {
        "municipality": "Name der Gemeinde, sollte mit dem Namen auf https://www.abfall-lro.de/de/abfuhrtermine/ übereinstimmen (einschließlich Unterregion in Klammern)",
        "black_rhythm": "Leerungsrythmus der schwarzen Tonne",
        "green_rhythm": "Leerungsrythmus der grünen Tonne",
        "black_seasonal": "Ankreuzen, wenn die schwarzen Tonnen nur saisonal geleert werden",
        "green_seasonal": "Ankreuzen, wenn die Grünen Tonnen nur saisonal geleert werden",
    },
}


class Source:
    def __init__(
        self,
        municipality: str,
        black_rhythm: RHYTHMS,
        green_rhythm: RHYTHMS,
        black_seasonal: bool = False,
        green_seasonal: bool = False,
    ) -> None:
        self._municipality: str = municipality
        self._ics = ICS(regex=r"Leerung (.*)")
        self._letters: str | None = None
        self._black_rhythm = black_rhythm
        self._green_rhythm = green_rhythm
        self._black_seasonal = black_seasonal
        self._green_seasonal = green_seasonal

    def fetch_letter(self) -> None:
        r = requests.get(API_URL)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a")
        relevant_links: list[Tag] = []
        for link in links:
            if (
                isinstance(link, Tag)
                and isinstance(href := link.get("href"), str)
                and href.startswith("/default")
                and href.endswith(".pdf")
            ):
                relevant_links.append(link)

        mun_link: str | None = None
        municipalities = []
        for link in relevant_links:
            text = link.text.strip()
            if isinstance(link.next_sibling, NavigableString):
                text += " " + link.next_sibling.strip()

            municipalities.append(text)
            if self._municipality.lower().replace(" ", "").replace("(", "").replace(
                ")", ""
            ) == text.lower().replace(" ", "").replace("(", "").replace(")", ""):
                mun_link = link.get("href")
                break
        if mun_link is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", self._municipality, municipalities
            )

        self._letters = mun_link.split("/")[-1].split(".")[0]

    def fetch(self) -> list[Collection]:
        fresh_letter = False
        if self._letters is None:
            fresh_letter = True
            self.fetch_letter()

        try:
            return self.get_collections_per_year()
        except Exception:
            if fresh_letter:
                raise
            return self.get_collections_per_year()

    def get_collections_per_year(self) -> list[Collection]:
        now = datetime.now()
        year = now.year
        collections = self.get_collections(year)
        if now.month != 12:
            return collections
        try:
            collections += self.get_collections(year + 1)
        except Exception:
            pass
        return collections

    def get_collections(self, year: int) -> list[Collection]:
        args = {
            "letters": self._letters,
            "year": year,
            "black": self._black_rhythm,
            "green": self._green_rhythm,
            "yellow": "y",
            "blue": "y",
        }
        if self._black_seasonal:
            args["bsaison"] = "y"
        if self._green_seasonal:
            args["gsaison"] = "y"

        # get json file
        r = requests.get(ICAL_URL, params=args)
        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1].split()[0])))

        return entries
