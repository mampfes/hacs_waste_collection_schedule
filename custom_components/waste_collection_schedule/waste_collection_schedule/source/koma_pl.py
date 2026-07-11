import urllib.parse
from datetime import datetime

from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

TITLE = "KOMA"
DESCRIPTION = "Source for KOMA waste collection (e.g. Nowy Dwór Gdański, Poland)."
URL = "https://koma.pl"
COUNTRY = "pl"

API_URL = "https://bok.koma.pl"

TEST_CASES = {
    "Nowy Dwór Gdański, Kanałowa 5": {
        "gmina": "Nowy Dwór Gdański",
        "miejscowosc": "Nowy Dwór Gdański",
        "ulica": "Kanałowa",
        "numer_domu": "5",
    },
    "Nowy Dwór Gdański, Kanałowa 4/1": {
        "gmina": "Nowy Dwór Gdański",
        "miejscowosc": "Nowy Dwór Gdański",
        "ulica": "Kanałowa",
        "numer_domu": "4/1",
    },
}

ICON_MAP = {
    "Zmieszane": Icons.GENERAL_WASTE,
    "Bio": Icons.ORGANIC,
    "Odpady zielone": Icons.GARDEN,
    "Papier": Icons.PAPER,
    "Szkło": Icons.GLASS,
    "Metale i tworzywa sztuczne": Icons.RECYCLING,
    "Gabaryty": Icons.BULKY,
    "Elektro": Icons.ELECTRONICS,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Open https://koma.pl/harmonogram-odpadow/ and step through the dropdowns "
        "(Wybierz Miasto -> miejscowość -> ulica -> numer domu) to find the exact "
        "spelling of your gmina, town, street and house number."
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "gmina": "Commune (gmina)",
        "miejscowosc": "Town",
        "ulica": "Street",
        "numer_domu": "House number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "gmina": "Name of the commune (gmina) as listed on koma.pl.",
        "miejscowosc": "Name of the town/village.",
        "ulica": "Street name (leave empty for towns without streets).",
        "numer_domu": "House number.",
    },
}


class Source:
    def __init__(
        self, gmina: str, miejscowosc: str, numer_domu: str | int, ulica: str = ""
    ):
        self._gmina = str(gmina).strip()
        self._miejscowosc = str(miejscowosc).strip()
        self._ulica = str(ulica).strip()
        self._numer_domu = str(numer_domu).strip()

    def _get_json(self, session, path_segments, params=None):
        url = (
            API_URL
            + "/"
            + "/".join(urllib.parse.quote(segment) for segment in path_segments)
        )
        response = session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")

        # The API "prefix" path segment equals the gmina name.
        prefix = self._gmina

        # 1. Resolve the property id (numer_posesji) for the given house number.
        posesje_path = ["api", "posesje", prefix, self._gmina, self._miejscowosc]
        if self._ulica:
            posesje_path.append(self._ulica)
        properties = self._get_json(session, posesje_path)

        if not properties:
            if self._ulica:
                streets = self._get_json(
                    session, ["api", "ulice", prefix, self._gmina, self._miejscowosc]
                )
                raise SourceArgumentNotFoundWithSuggestions(
                    "ulica",
                    self._ulica,
                    sorted({s["ulica"] for s in streets if s.get("ulica")}),
                )
            raise SourceArgumentNotFoundWithSuggestions(
                "miejscowosc", self._miejscowosc, []
            )

        match = next(
            (
                p
                for p in properties
                if str(p.get("numer_domu")).strip().casefold()
                == self._numer_domu.casefold()
            ),
            None,
        )
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "numer_domu",
                self._numer_domu,
                sorted({str(p.get("numer_domu")) for p in properties}),
            )

        # 2. Fetch the schedule for the resolved property.
        schedule = self._get_json(
            session,
            ["api", "apiharmonogram"],
            {"value": f"{prefix}/{match['numer_posesji']}"},
        )

        entries: list[Collection] = []
        for collection in schedule.get("odbior", []):
            try:
                day = datetime.strptime(collection["data"], "%Y-%m-%d").date()
            except (ValueError, KeyError):
                continue
            waste_type = collection.get("typ", "")
            entries.append(Collection(day, waste_type, icon=ICON_MAP.get(waste_type)))
        return entries
