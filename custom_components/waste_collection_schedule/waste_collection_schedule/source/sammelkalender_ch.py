from datetime import datetime
from typing import Literal

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

TITLE = "Sammelkalender.ch"
DESCRIPTION = "Source for Sammelkalender.ch."
URL = "https://info.sammelkalender.ch"
TEST_CASES = {
    "zeba Baar Aberenrain 10": {
        "service_provider": "zeba",
        "municipality": "Baar",
        "street": "Aberenrain",
        "hnr": 10,
    },
    "zkri Rothenthurm": {
        "service_provider": "zkri",
        "municipality": "Rothenthurm",
    },
    "ZKRI, Schwyz Seewen": {
        "service_provider": "zkri",
        "municipality": "Schwyz",
        "street": "Seewen",
    },
    "Real Luzern, Meggen": {
        "service_provider": "real_luzern",
        "municipality": "Meggen",
    },
    "Real Luzern, Malters, Bodenmättli": {
        "service_provider": "real_luzern",
        "municipality": "Malters",
        "street": "Bodenmättli",
    },
    "Zaku Altdorf dag": {
        "service_provider": "zaku",
        "municipality": "Altdorf",
        "street": "dag",
    },
}


ICON_MAP = {
    "Kehricht": "mdi:trash-can",
    "Christbaum": "mdi:pine-tree",
    "Grüngut": "mdi:leaf",
    "Karton": "mdi:package-variant-closed",
    "Papier": "mdi:newspaper",
    "Alteisen/Metall": "mdi:screw-flat-top",
}

SERVICES = {
    "zeba": {
        "title": "Zeba",
        "url": "https://www.zebazug.ch",
        "api_url_search": "https://www.zeba.sammelkalender.ch/kunden_WANN_auswahl_form.php",
        "api_url_bin": "https://www.zeba.sammelkalender.ch/kunden_sammlung_ausw_cont.php",
    },
    "zkri": {
        "title": "ZKRI",
        "url": "https://zkri.ch",
        "api_url_search": "https://daten.zkri.ch/web/Sammelkalender/kunden_WANN_auswahl_form.php",
        "api_url_bin": "https://daten.zkri.ch/web/Sammelkalender/kunden_sammlung_ausw_cont.php",
    },
    "real_luzern": {
        "title": "Real Luzern",
        "url": "https://www.realluzern.ch",
        "api_url_search": "https://www.real.sammelkalender.ch/app/appSelect.php",
        "api_url_bin": "https://www.real.sammelkalender.ch/app/appSammeldaten.php",
    },
    "zaku": {
        "title": "ZAKU Entsorgung",
        "url": "https://www.zaku.ch",
        "api_url_search": "https://www.zaku.sammelkalender.ch/appSelect.php",
        "api_url_bin": "https://www.zaku.sammelkalender.ch/appSammeldaten.php",
    },
}

EXTRA_INFO = [
    {
        "title": s["title"],
        "url": s["url"],
        "default_params": {
            "service_provider": key,
        },
    }
    for key, s in SERVICES.items()
]


PROVIDER_LITERALS = Literal["zeba", "zkri", "real_luzern", "zaku"]


API_URL = ""


class Source:
    def __init__(
        self,
        service_provider: PROVIDER_LITERALS,
        municipality: str,
        street: str | None = None,
        hnr: str | int | None = None,
    ) -> None:
        service_provider_str = service_provider.lower()
        if service_provider not in SERVICES:
            raise SourceArgumentNotFoundWithSuggestions(
                "service_provider", service_provider, list(SERVICES.keys())
            )
        self._search_url = SERVICES[service_provider_str]["api_url_search"]
        self._bin_url = SERVICES[service_provider_str]["api_url_bin"]

        self._municipality: str = municipality
        self._street: str | None = street
        self._hnr: str | None = str(hnr) if hnr is not None else None

        self._municipality_id: str | None = None
        self._address_id: str | None = None

    @staticmethod
    def _compare(s1: str, s2: str | list[str]) -> bool:
        if isinstance(s2, str):
            s2 = [s2]

        for s in s2:
            if s1.lower().replace(" ", "").replace("str.", "straße").replace(
                "strasse", "straße"
            ) == s.lower().replace(" ", "").replace("str.", "straße").replace(
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

        r = requests.get(self._search_url, params=params)
        r.raise_for_status()
        streets = r.json()

        if len(streets) == 0:
            return []
        return streets

    def _fetch_sage(self) -> None:
        sages = self._get_streets(sage=True)
        if not sages:
            return
        if len(sages) == 1:
            self._address_id = sages[0]["SAGEid"]
            return
        for sage in sages:
            if not self._street:
                street_names = list(
                    {s.get("STRname") or s.get("SAGEname") for s in sages}
                )
                raise SourceArgumentRequiredWithSuggestions(
                    "street", "Street required for this municipality", street_names
                )
            if self._compare(self._street, [sage["SAGEabk"], sage["SAGEname"]]):
                self._address_id = sage["SAGEid"]
                break
        if not self._address_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                list({s["SAGEname"] for s in sages}),
            )

    def _fetch_street(self) -> None:
        streets = self._get_streets()
        
        # switch to Sammelgebiete if API either returns no streets or one dummy street
        if (
            not streets
            or len(streets) == 1
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
        r = requests.get(self._search_url, params=params)
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
        r = requests.get(self._bin_url, params=params)
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
