"""MontpellierCollectionReference retrieval and parsing, using the pipeline HTTP session."""

from datetime import date, timedelta
from typing import Any

from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.preprocessors import Preprocessor, Schedule
from waste_collection_schedule.retrievers import Request

DAY_CODE_MAP = {"L": 0, "M": 1, "W": 2, "J": 3, "V": 4, "S": 5, "D": 6}
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
CSV_URL = "https://data.montpellier3m.fr/sites/default/files/ressources/MMM_MMM_ReferentielCollecte.csv"  # codespell:ignore ressources


def _normalize_street(name: str) -> str:
    parts = name.upper().strip().split()
    if parts and parts[0] in STREET_TYPE_MAP:
        parts[0] = STREET_TYPE_MAP[parts[0]]
    return " ".join(parts)


def _schedules_from_day_code(day_code: str, key: str, weeks: int = 8) -> list[Schedule]:
    # The provider's projection starts strictly after today, including when
    # today is itself a collection day.
    tomorrow = date.today() + timedelta(days=1)
    return [
        Schedule(
            key=key,
            start=recurrence.next_weekday(DAY_CODE_MAP[code], on_or_after=tomorrow),
            count=weeks,
        )
        for code in day_code
        if code in DAY_CODE_MAP
    ]


class _CalendarClient:
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

    def parse(self, rows):
        normalized_input = _normalize_street(self._street_name)
        matching_rows = []
        for row in rows:
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
        schedules = []
        for row in matching_rows:
            for jour_field, typ_field, label in WASTE_TYPES:
                jour = (row.get(jour_field) or "").strip()
                typ_col = (row.get(typ_field) or "").strip()
                if not jour or jour in ("NR", "RDV"):
                    continue
                if typ_col not in ("PAP", "PAV", "DEP"):
                    continue
                schedules.extend(_schedules_from_day_code(jour, label))
        if not schedules:
            raise SourceArgumentNotFound(
                "street_name",
                f"Address found but no collection schedule available for '{self._street_name}'",
            )
        return schedules


class CollectionSchedules(Preprocessor[Any, Schedule]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[Schedule]:
        if source is None:
            raise ValueError("Collection schedules require a source")
        client = _CalendarClient(**source.params)
        return client.parse(response)


calendar_retriever = Request(CSV_URL, timeout=120)
