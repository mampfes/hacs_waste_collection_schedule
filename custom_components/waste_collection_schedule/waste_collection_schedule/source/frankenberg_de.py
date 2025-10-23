from datetime import datetime

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.ICS import ICS

TITLE = "Stadt Frankenberg (Eder)"
DESCRIPTION = "Source for Stadt Frankenberg (Eder)."
URL = "https://www.frankenberg.de/"
TEST_CASES = {
    "Viermünden": {"district": "Viermünden"},
    "FKB-Kernstadt, Futterhof": {"district": "FKB-Kernstadt", "street": "Futterhof"},
}

ICON_MAP = {
    "Trash": "mdi:trash-can",
    "Glass": "mdi:bottle-soda",
    "Bio": "mdi:leaf",
    "Paper": "mdi:package-variant",
    "Recycle": "mdi:recycle",
}


API_URL = "https://abfall.frankenberg.de/online-dienste/"


class Source:
    def __init__(self, district: str, street: str | None = None):
        self._district: str = district
        self._street: str | None = street
        self._ics = ICS(regex=r"(.*) am \d{2}.\d{2}.\d{4}")
        self._district_id: str | None = None
        self._street_id: str | None = None

    def _match_district(self, district: str) -> bool:
        return district.lower().replace(" ", "").replace('"', "").replace(
            "-", ""
        ) == self._district.lower().replace(" ", "").replace('"', "").replace("-", "")

    def _match_street(self, street: str) -> bool:
        if self._street is None:
            return False

        return street.lower().replace(" ", "").replace('"', "").replace(
            "-", ""
        ).replace("str.", "straße").replace("straße", "strasse").replace(
            ".", ""
        ) == self._street.lower().replace(
            " ", ""
        ).replace(
            '"', ""
        ).replace(
            "-", ""
        ).replace(
            "str.", "straße"
        ).replace(
            "straße", "strasse"
        ).replace(
            ".", ""
        )

    def fetch(self) -> list[Collection]:
        fresh_ids = False
        if self._district_id is None:
            fresh_ids = True
            self._get_ids()
        try:
            return self._get_collections()
        except Exception:
            if fresh_ids:
                raise
            self._get_ids()
            return self._get_collections()

    def _get_collections(
        self,
    ) -> list[Collection]:
        now = datetime.now()
        entries = self._get_collections_by_year(now.year)
        if now.month != 12:
            return entries
        try:
            entries.extend(self._get_collections_by_year(now.year + 1))
        except Exception:
            pass
        return entries

    def _get_collections_by_year(self, year: int) -> list[Collection]:
        if self._street_id is not None:
            data = {
                "year": year,
                "ak_bezirk": 1,
                "ak_ortsteil": self._district_id,
                "ak_strasse": self._street_id,
                "alle_arten": "",
                "datum_von": datetime(year, 1, 1).strftime("%d.%m.%Y"),
                "datum_bis": datetime(year, 12, 31).strftime("%d.%m.%Y"),
            }
        else:
            data = {
                "year": year,
                "ak_bezirk": 1,
                "ak_ortsteil": self._district_id,
                "alle_arten": "",
                "datum_von": datetime(year, 1, 1).strftime("%d.%m.%Y"),
                "datum_bis": datetime(year, 12, 31).strftime("%d.%m.%Y"),
            }
        
        r = requests.post(
            "https://abfall.frankenberg.de/module/abfallkalender/generate_ical.php",
            data=data,
        )

        r.raise_for_status()

        dates = self._ics.convert(r.text)
        entries = []
        for d in dates:
            entries.append(Collection(d[0], d[1], ICON_MAP.get(d[1])))

        return entries

    def _get_ids(self) -> None:
        r = requests.get(
            "https://abfall.frankenberg.de/module/abfallkalender/get_ortsteile.php",
            params={"bez_id": 1},
        )
        r.raise_for_status()
        # f.ak_ortsteil.options[0].text = 'Bitte wählen';f.ak_ortsteil.length = 2;f.ak_ortsteil.options[1].value = '1-1';
        result = r.text.split(";")[
            1:-2
        ]  # remove first element (Bitte wählen) and last element (selectedIndex)

        self._district_id = None
        district_names = []

        for i in range(0, len(result), 3):
            id = result[i + 1].split("'")[1]
            name = result[i + 2].split("'")[1]
            district_names.append(name)
            if self._match_district(name):
                self._district_id = id
                break

        if self._district_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                argument="district",
                value=self._district,
                suggestions=district_names,
            )

        if not self._district_id.endswith("-0"):
            self._get_street_id()

    def _get_street_id(self) -> None:
        if not self._district_id:
            raise ValueError("No district id found")
        r = requests.get(
            "https://abfall.frankenberg.de/module/abfallkalender/get_strassen.php",
            params={"ot_id": self._district_id.split("-")[0]},
        )
        r.raise_for_status()

        result = r.text.split(";")[
            1:-2
        ]  # remove first element (Bitte wählen) and last element (selectedIndex)

        names = []
        self._street_id = None

        for i in range(0, len(result), 3):
            id = result[i + 1].split(" = ")[1]
            name = result[i + 2].split("'")[1]
            names.append(name)
            if self._match_street(name):
                self._street_id = id
                break

        if self._street_id is None:
            if self._street is None:
                raise SourceArgumentRequiredWithSuggestions(
                    argument="street",
                    reason="street is required for this district",
                    suggestions=names,
                )
            else:
                raise SourceArgumentNotFoundWithSuggestions(
                    argument="street", value=self._street, suggestions=names
                )
