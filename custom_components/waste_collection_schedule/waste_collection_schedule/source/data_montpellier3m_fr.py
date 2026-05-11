import csv
import io
from datetime import date, timedelta

import requests
from waste_collection_schedule import Collection
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Montpellier Méditerranée Métropole"
DESCRIPTION = "Source for waste collection schedules in Montpellier Méditerranée Métropole, France."
URL = "https://data.montpellier3m.fr"
COUNTRY = "fr"

TEST_CASES = {
    "Montpellier, Rue Parlier 3": {
        "street_name": "Rue Parlier",
        "house_number": 3,
        "commune": "MONTPELLIER",
    },
    "Montpellier, Rue Parlier 8": {
        "street_name": "Rue Parlier",
        "house_number": 8,
        "commune": "MONTPELLIER",
    },
    "Lattes, Avenue de Montpellier": {
        "street_name": "Avenue de Montpellier",
        "commune": "LATTES",
    },
    "Castelnau-le-Lez, Chemin des Alouettes": {
        "street_name": "Chemin des Alouettes",
        "commune": "CASTELNAU-LE-LEZ",
    },
}

ICON_MAP = {
    "Ordures ménagères": "mdi:trash-can",
    "Tri sélectif": "mdi:recycle",
    "Biodéchets": "mdi:leaf",
    "Encombrants": "mdi:truck-remove",
}

DAY_CODE_MAP = {
    "L": 0,
    "M": 1,
    "W": 2,
    "J": 3,
    "V": 4,
    "S": 5,
    "D": 6,
}

STREET_TYPE_MAP = {
    "R": "RUE",
    "AV": "AVENUE",
    "CHE": "CHEMIN",
    "IMP": "IMPASSE",
    "ALL": "ALLEE",
    "RTE": "ROUTE",
    "PL": "PLACE",
    "BD": "BOULEVARD",
    "SQ": "SQUARE",
    "CI": "CITE",
    "DOM": "DOMAINE",
    "LOT": "LOTISSEMENT",
    "LOTISSEMENT": "LOTISSEMENT",
    "GR": "GRAND RUE",
    "PLAN": "PLAN",
    "COUR": "COUR",
}

WASTE_TYPES = [
    ("om_jour", "om_typ_col", "Ordures ménagères"),
    ("ts_jour", "ts_typ_col", "Tri sélectif"),
    ("bio_jour", "bio_typ_co", "Biodéchets"),
    ("enc_u_jour", "enu_typ_co", "Encombrants"),
]

CSV_URL = "https://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_ReferentielCollecte.csv"

PARAM_TRANSLATIONS = {
    "en": {
        "street_name": "Street name",
        "house_number": "House number",
        "commune": "Commune (city)",
    },
    "fr": {
        "street_name": "Nom de rue",
        "house_number": "Numéro",
        "commune": "Commune",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "street_name": "Full street name, e.g. 'Rue Parlier' or 'Avenue de Montpellier'",
        "house_number": "House number (optional but recommended for accurate results)",
        "commune": "Commune name in capitals, e.g. 'MONTPELLIER', 'LATTES'. Helps when a street name appears in multiple communes.",
    },
    "fr": {
        "street_name": "Nom complet de la rue, ex : 'Rue Parlier' ou 'Avenue de Montpellier'",
        "house_number": "Numéro de maison (facultatif mais recommandé)",
        "commune": "Nom de la commune en majuscules, ex : 'MONTPELLIER', 'LATTES'. Utile si la rue existe dans plusieurs communes.",
    },
}


def _normalize_street(name: str) -> str:
    parts = name.upper().strip().split()
    if parts and parts[0] in STREET_TYPE_MAP:
        parts[0] = STREET_TYPE_MAP[parts[0]]
    return " ".join(parts)


def _dates_from_day_code(day_code: str, weeks: int = 8) -> list[date]:
    today = date.today()
    result = []
    for code in day_code:
        if code not in DAY_CODE_MAP:
            continue
        target_wd = DAY_CODE_MAP[code]
        curr_wd = today.weekday()
        diff = (target_wd - curr_wd) % 7
        if diff == 0:
            diff = 7
        for week in range(weeks):
            result.append(today + timedelta(days=diff + week * 7))
    return result


class Source:
    def __init__(
        self,
        street_name: str,
        house_number: int | str | None = None,
        commune: str | None = None,
    ):
        self._street_name = street_name.strip()
        self._house_number = (
            str(house_number).strip() if house_number is not None else None
        )
        self._commune = commune.strip().upper() if commune else None

    def fetch(self) -> list[Collection]:
        response = requests.get(CSV_URL, timeout=120)
        response.raise_for_status()

        content = response.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))

        normalized_input = _normalize_street(self._street_name)

        matching_rows = []
        for row in reader:
            voie = (row.get("nom_voie") or "").strip()
            if not voie:
                continue

            if _normalize_street(voie) != normalized_input:
                continue

            if (
                self._commune
                and row.get("commune", "").strip().upper() != self._commune
            ):
                continue

            if self._house_number is not None:
                row_num = (row.get("numero") or "").strip()
                if row_num != self._house_number:
                    continue

            matching_rows.append(row)

        if not matching_rows:
            raise SourceArgumentNotFound(
                "street_name",
                f"No results found for '{self._street_name}'"
                + (f" in {self._commune}" if self._commune else "")
                + (f" at number {self._house_number}" if self._house_number else ""),
            )

        entries: list[Collection] = []
        seen: set[tuple[str, date]] = set()

        for row in matching_rows:
            for jour_field, typ_field, label in WASTE_TYPES:
                jour = (row.get(jour_field) or "").strip()
                typ_col = (row.get(typ_field) or "").strip()

                if not jour or jour in ("NR", "RDV"):
                    continue
                if typ_col not in ("PAP", "PAV", "DEP"):
                    continue

                for d in _dates_from_day_code(jour):
                    key = (label, d)
                    if key not in seen:
                        seen.add(key)
                        entries.append(
                            Collection(
                                date=d,
                                t=label,
                                icon=ICON_MAP.get(label),
                            )
                        )

        if not entries:
            raise SourceArgumentNotFound(
                "street_name",
                f"Address found but no collection schedule available for '{self._street_name}'",
            )

        return entries
