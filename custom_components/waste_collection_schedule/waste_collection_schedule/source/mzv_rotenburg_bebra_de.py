import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "MZV Rotenburg"
DESCRIPTION = "Source for MZV Rotenburg."
URL = "https://www.mzv-rotenburg-bebra.de"
TEST_CASES = {
    # "Rotenburg an der Fulda 2 Ost": {
    #     "city": "rote",
    #     "yellow_route": "2",
    #     "paper_route": "Ost",
    # },
    "bullshit": {
        "city": "asdf",
        "yellow_route": "2",
        "paper_route": "Ost",
    },
}


ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}

PARAM_TRANSLATIONS = {
    "de": {
        "city": "Ort",
        "yellow_route": "Gelbe Tonne Rute",
        "paper_route": "Papier Rute",
    }
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "yellow_route": "Used if there are multiple routes for the yellow bin collection. E.g 'Rotenburg - Kernstadt' has yellow bin collection routes `1`,`2`,`3` and `4`.",
        "paper_route": "Used if there are multiple routes for the paper collection. E.g 'Rotenburg - Kernstadt' has paper collection routes `West` and `Ost`.",
        "city": "Should be spelled exactly like in the `ort` URL parameter of the link url shown on the website: https://www.mzv-rotenburg-bebra.de//webapp.html Like: `lisp`, `rot`, `bebra`, ...",
    },
    "de": {
        "city": "Genau wie in der `ort` URL-Parameter des Links auf der Website: https://www.mzv-rotenburg-bebra.de//webapp.html. Z.B. `lisp`, `rot`, `bebra`, ...",
        "yellow_route": "Wird verwendet, wenn es mehrere Routen für die Gelbe Tonne gibt. Z.B. hat 'Rotenburg - Kernstadt' Gelbe Tonne Routen `1`,`2`,`3` und `4`.",
        "paper_route": "Wird verwendet, wenn es mehrere Routen für die Papierabholung gibt. Z.B. hat 'Rotenburg - Kernstadt' Papierabholrouten `West` und `Ost`.",
    },
}


API_URL = "https://www.mzv-rotenburg-bebra.de/entsorgung.php"


class Source:
    def __init__(
        self, city: str, yellow_route: str | None = None, paper_route: str | None = None
    ):
        self._city: str = city
        self._yellow_route: str | None = yellow_route
        self._paper_route: str | None = paper_route
        self._ics = ICS(title_template="{{date.summary}}\n\t{{date.location}}")

    def _get_possible_cities(self) -> list[str]:
        r = requests.get(
            "https://www.mzv-rotenburg-bebra.de//webapp.html",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.content, "html.parser")
        links = soup.find_all(
            lambda tag: tag
            and tag.name == "a"
            and tag.get("href")
            and "entsorgung.php?ort=" in tag["href"]
        )
        return [link["href"].split("?ort=")[1] for link in links]

    def fetch(self) -> list[Collection]:
        args = {
            "ort": self._city,
        }
        r = requests.get(API_URL, params=args, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        try:
            dates = self._ics.convert(r.text)
        except ValueError:
            try:
                cities = self._get_possible_cities()
            except Exception:
                raise SourceArgumentNotFound(
                    "city",
                    self._city,
                    "make sure the city is spelled exactly like in the link of the website https://www.mzv-rotenburg-bebra.de//webapp.html",
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "city",
                self._city,
                cities,
            )

        entries = []

        for d in dates:
            bin_type, location = d[1].split("\n\t", 1)
            bin_type = bin_type.removeprefix("Entsorgung").strip()
            if bin_type.lower().replace(" ", "") == "gelbetonne" and self._yellow_route:
                if self._yellow_route not in location:
                    continue
            if bin_type.lower().replace(" ", "") == "papier" and self._paper_route:
                if self._paper_route not in location:
                    continue
            entries.append(Collection(d[0], bin_type, ICON_MAP.get(bin_type)))

        return entries
