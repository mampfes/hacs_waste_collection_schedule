import logging
from datetime import datetime

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "SUIBR"
DESCRIPTION = "Source for SUIBR (Nidwalden) waste collection."
URL = "https://www.suibr.ch"
COUNTRY = "ch"

SOURCE_CODEOWNERS = ["@AlpenGlowNW"]

PARAM_TRANSLATIONS = {
    "en": {
        "municipality": "Municipality",
        "street": "Street",
        "hnr": "House Number",
    },
    "de": {
        "municipality": "Gemeinde",
        "street": "Straße",
        "hnr": "Hausnummer",
    },
}

TEST_CASES = {
    "Beckenried": {
        "municipality": "Beckenried",
        "street": "Acheri",
        "hnr": 1,
    },
    "Buochs": {
        "municipality": "Buochs",
        "street": "Aamättli",
        "hnr": 2,
    },
    "Dallenwil": {
        "municipality": "Dallenwil",
        "street": "Aawasserstrasse",
        "hnr": 11,
    },
    "Emmetten": {
        "municipality": "Emmetten",
        "street": "Altberg",
        "hnr": 1,
    },
    "Ennetbürgen": {
        "municipality": "Ennetbürgen",
        "street": "Abendweg",
        "hnr": 11,
    },
    "Ennetmoos": {
        "municipality": "Ennetmoos",
        "street": "Allweg",
        "hnr": 2,
    },
    "Hergiswil": {
        "municipality": "Hergiswil",
        "street": "Aescheli",
        "hnr": 1,
    },
    "Oberdorf": {
        "municipality": "Oberdorf",
        "street": "Aawasserstrasse",
        "hnr": 1,
    },
    "Stans": {
        "municipality": "Stans",
        "street": "Ächerli",
        "hnr": 1,
    },
    "Stansstad": {
        "municipality": "Stansstad",
        "street": "Acheregg",
        "hnr": 1,
    },
    "Wolfenschiessen": {
        "municipality": "Wolfenschiessen",
        "street": "Aegerten",
        "hnr": 1,
    },
}

ICON_MAP = {
    "Kehricht": Icons.GENERAL_WASTE,
    "Christbaum": Icons.CHRISTMAS_TREE,
    "Grüngut": Icons.ORGANIC,
    "Karton": Icons.PAPER,
    "Papier": Icons.PAPER,
    "Alteisen/Metall": Icons.METAL,
}

MUNICIPALITIES = [
    "Beckenried",
    "Buochs",
    "Dallenwil",
    "Emmetten",
    "Ennetbürgen",
    "Ennetmoos",
    "Hergiswil",
    "Oberdorf",
    "Stans",
    "Stansstad",
    "Wolfenschiessen",
]

API_URL_SEARCH = "https://www.kvvnw.sammelkalender.ch/kunden_WANN_auswahl_form.php"
API_URL_BIN = "https://www.kvvnw.sammelkalender.ch/kunden_sammlung_ausw_cont.php"

_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        municipality: str,
        street: str | None = None,
        hnr: str | int | None = None,
    ) -> None:
        if municipality not in MUNICIPALITIES:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", municipality, MUNICIPALITIES
            )

        self._municipality: str = municipality
        self._street: str | None = street
        self._hnr: str | None = str(hnr) if hnr is not None else None

        self._municipality_id: str | None = None
        self._address_id: str | None = None

    @staticmethod
    def _compare(s1: str | None, s2: str | list[str] | None) -> bool:
        if s1 is None or s2 is None:
            return False
        if isinstance(s2, str):
            s2 = [s2]

        for s in s2:
            if s is None:
                continue
            if s1.strip().lower().replace(" ", "").replace("str.", "straße").replace(
                "strasse", "straße"
            ) == s.strip().lower().replace(" ", "").replace("str.", "straße").replace(
                "strasse", "straße"
            ):
                return True
        return False

    def _get_streets(self, sage: bool = False) -> list[dict]:
        params: dict[str, str | int | None] = {
            "optGem": self._municipality_id,
            "Jahr": None,
        }
        if sage:
            params["fuerSage"] = 1
        else:
            params["fuerStr"] = 1

        r = requests.get(API_URL_SEARCH, params=params)
        r.raise_for_status()
        streets = r.json()

        if len(streets) == 0:
            return []
        return streets

    def _fetch_sage(self) -> None:
        sages = self._get_streets(sage=True)
        if not sages:
            return
        # check: only one sage exists?
        if len(sages) == 1:
            self._address_id = sages[0]["SAGEid"]
            return
        # check: street parameter defined?
        if not self._street:
            sage_names = list({s.get("STRname") or s.get("SAGEname") for s in sages})
            # by default use first Sammelgebiet and log a Warning
            # (prevents breaking changes: existing users may have no street configured, because it was not mandatory previously)
            self._address_id = sages[0]["SAGEid"]
            _LOGGER.warning(
                "No Sammelgebiet configured for this municipality. Using default Sammelgebiet '%s'. To configure, insert for the parameter 'street': %s",
                sages[0]["SAGEname"],
                ", ".join(sage_names),
            )
            return
        # otherwise find correct sage
        for sage in sages:
            if self._compare(self._street, [sage["SAGEabk"], sage["SAGEname"]]):
                self._address_id = sage["SAGEid"]
                return
        if self._address_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                list({s["SAGEname"] for s in sages}),
            )

    def _fetch_street(self) -> None:
        streets = self._get_streets()

        # switch to Sammelgebiete if API either returns no streets or one dummy street
        if not streets or (
            len(streets) == 1
            and streets[0].get("STRname") is None
            and streets[0].get("SAGEid") is not None
        ):
            self._fetch_sage()
            return

        self._address_id = None
        street_matches = []
        if len(streets) == 1:
            street_matches = streets
        else:
            if not self._street:
                street_names = list(
                    {s.get("STRname") or s.get("SAGEname") for s in streets}
                )
                raise SourceArgumentRequiredWithSuggestions(
                    "street", "Street required for this municipality", street_names
                )
            for street in streets:
                if self._compare(street["STRname"], self._street):
                    street_matches.append(street)

        if not street_matches:
            raise ValueError(
                f"Invalid street: {self._street}, use one of {list({s['STRname'] for s in streets})}"
            )

        for street in street_matches:
            if not street["STRhausnr"]:
                self._address_id = street["SAGEid"]
                break

            if self._hnr is None:
                raise SourceArgumentRequiredWithSuggestions(
                    "hnr",
                    "House number required for this street",
                    [s["STRhausnr"] for s in street_matches],
                )
            if self._compare(street["STRhausnr"], self._hnr):
                self._address_id = street["SAGEid"]
                break

        if not self._address_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "hnr",
                self._hnr,
                list({s["STRhausnr"] for s in street_matches}),
            )

    def _fetch_ids(self) -> None:
        params = {
            "optGem": "GEM",
            "Jahr": None,
        }

        # get json file
        r = requests.get(API_URL_SEARCH, params=params)
        r.raise_for_status()
        self._municipality_id = None
        for mun in r.json():
            if self._compare(mun["GEMname"], self._municipality):
                self._municipality_id = mun["GEMid"]
                break
        if not self._municipality_id:
            raise ValueError(
                f"Invalid municipality: {self._municipality}, use one of {[m['GEMname'] for m in r.json()]}"
            )

        self._fetch_street()

    def fetch(self) -> list[Collection]:
        fresh_ids = False
        if self._municipality_id is None:
            fresh_ids = True
            self._fetch_ids()
        try:
            return self._get_collections()
        except Exception:
            if fresh_ids:
                raise
            self._fetch_ids()
            return self._get_collections()

    def _get_collections(self) -> list[Collection]:
        today = datetime.now()
        year = today.year
        entries = self._get_collections_year(year)
        if today.month == 12:
            try:
                entries += self._get_collections_year(year + 1)
            except Exception:
                pass
        return entries

    def _get_collections_year(self, year: int) -> list[Collection]:
        if self._municipality is None:
            raise ValueError("Municipality required")

        params: dict[str, str | int | None] = {
            "nGem": self._municipality_id,
            "nAbar": "null",
            "nSage": self._address_id,
            "sDatum": "",
            "delsel": "no",
            "jahr1": year,
        }
        r = requests.get(API_URL_BIN, params=params)
        r.raise_for_status()

        entries = []
        for d in r.json():
            date = datetime.strptime(d["DATUM"], "%Y-%m-%d").date()
            bin_types = d["AbarOne"]
            if bin_types is None:
                continue
            for bin_type in bin_types.split("-"):
                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
