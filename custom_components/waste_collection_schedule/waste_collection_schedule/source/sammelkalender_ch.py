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
        # --- FIX: robust handling and correct key check ---
        if not service_provider:
            raise SourceArgumentRequiredWithSuggestions(
                "service_provider", "Service provider required", list(SERVICES.keys())
            )
        service_provider_str = service_provider.lower()
        if service_provider_str not in SERVICES:
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

    # --- NEW: normalization & None-safe comparison ---
    @staticmethod
    def _normalize(s: str | None) -> str | None:
        if s is None:
            return None
        return (
            s.lower()
            .replace(" ", "")
            .replace("str.", "straße")
            .replace("strasse", "straße")
        )

    @staticmethod
    def _compare(s1: str | None, s2: str | list[str | None]) -> bool:
        if isinstance(s2, str) or s2 is None:
            s2 = [s2]
        n1 = Source._normalize(s1)
        for s in s2:
            n2 = Source._normalize(s)
            if n1 is not None and n2 is not None and n1 == n2:
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

        if not streets or len(streets) == 0:
            return []
        return streets

    def _fetch_sage(self) -> None:
        sages = self._get_streets(sage=True)
        if not sages:
            return
        if len(sages) == 1:
            self._address_id = sages[0].get("SAGEid")
            return

        for sage in sages:
            if not self._street:
                street_names = list({s.get("STRname") or s.get("SAGEname") for s in sages})
                raise SourceArgumentRequiredWithSuggestions(
                    "street", "Street required for this municipality", street_names
                )
            if self._compare(self._street, [sage.get("SAGEabk"), sage.get("SAGEname")]):
                self._address_id = sage.get("SAGEid")
                break

        if not self._address_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                self._street,
                list({s.get("SAGEname") for s in sages if s.get("SAGEname")}),
            )

    def _fetch_street(self) -> None:
        streets = self._get_streets()
        if not streets:
            # Fallback: municipality uses SAGE-style areas instead of classic streets
            self._fetch_sage()
            return

        self._address_id = None
        street_matches = []
        if len(streets) == 1:
            street_matches = streets
        else:
            if not self._street:
                street_names = list({s.get("STRname") or s.get("SAGEname") for s in streets})
                raise SourceArgumentRequiredWithSuggestions(
                    "street", "Street required for this municipality", street_names
                )
            for street in streets:
                name = street.get("STRname")
                if name and self._compare(name, self._street):
                    street_matches.append(street)

        if not street_matches:
            raise ValueError(
                f"Invalid street: {self._street}, use one of "
                f"{sorted({s.get('STRname') for s in streets if s.get('STRname')})}"
            )

        for street in street_matches:
            hausnr = street.get("STRhausnr")
            if not hausnr:
                # No house-number selection required, use SAGE id directly
                self._address_id = street.get("SAGEid")
                break

            if self._hnr is None:
                raise SourceArgumentRequiredWithSuggestions(
                    "hnr",
                    "House number required for this street",
                    [s.get("STRhausnr") for s in street_matches if s.get("STRhausnr")],
                )
            if self._compare(hausnr, self._hnr):
                self._address_id = street.get("SAGEid")
                break

        if not self._address_id:
            raise SourceArgumentNotFoundWithSuggestions(
                "hnr",
                self._hnr,
                list({s.get("STRhausnr") for s in street_matches if s.get("STRhausnr")}),
            )

    def _fetch_ids(self) -> None:
        params = {
            "optGem": "GEM",
            "Jahr": None,
        }

        r = requests.get(self._search_url, params=params)
        r.raise_for_status()
        self._municipality_id = None

        js = r.json() or []
        for mun in js:
            if self._compare(mun.get("GEMname"), self._municipality):
                self._municipality_id = mun.get("GEMid")
                break

        if not self._municipality_id:
            raise ValueError(
                f"Invalid municipality: {self._municipality}, use one of "
                f"{sorted({m.get('GEMname') for m in js if m.get('GEMname')})}"
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

        entries: list[Collection] = []
        data = r.json() or []
        for d in data:
            datum = d.get("DATUM")
            if not datum:
                continue
            date = datetime.strptime(datum, "%Y-%m-%d").date()
            bin_types = d.get("AbarOne")
            if not bin_types:
                continue
            for bin_type in str(bin_types).split("-"):
                icon = ICON_MAP.get(bin_type)  # Collection icon
                entries.append(Collection(date=date, t=bin_type, icon=icon))

        return entries
